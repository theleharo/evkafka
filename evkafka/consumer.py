import asyncio
import logging
import time
import typing
from asyncio import Future, Task
from itertools import chain

from aiokafka import (  # type: ignore
    AIOKafkaConsumer,
    ConsumerRebalanceListener,
    ConsumerRecord,
    ConsumerStoppedError,
)
from kafka import TopicPartition

from evkafka.config import ConsumerConfig
from evkafka.context import ConsumerCtx, MessageCtx

logger = logging.getLogger(__name__)


class RebalanceListener(ConsumerRebalanceListener):
    def __init__(
        self, on_rebalance_cb: typing.Callable[[], typing.Awaitable[None]]
    ) -> None:
        self.on_rebalance_cb = on_rebalance_cb

    async def on_partitions_revoked(self, revoked: list[TopicPartition]) -> None:
        await self.on_rebalance_cb()

    async def on_partitions_assigned(self, assigned: list[TopicPartition]) -> None:
        pass


class EVKafkaConsumer:
    def __init__(
        self,
        config: ConsumerConfig,
        messages_cb: typing.Callable[[MessageCtx, ConsumerCtx], typing.Awaitable[None]],
        loop_interval_ms: int = 1000,
        batch_max_size: int = 1,
    ) -> None:
        config = config.copy()
        self._messages_cb = messages_cb
        self._loop_interval_ms = loop_interval_ms
        self._batch_max_size = batch_max_size

        config_extra: dict[str, typing.Any] = {}
        self._topics = config.pop("topics")
        self._group_id = config.get("group_id")
        try:
            self._client_id = config["client_id"]
        except KeyError:
            self._client_id = "evkafka"
            config_extra["client_id"] = self._client_id

        self._auto_commit_mode = config.pop("auto_commit_mode", "pre-commit")
        assert self._auto_commit_mode in [
            "pre-commit",
            "post-commit",
        ], 'Unsupported auto commit mode. Supported modes are: "pre-commit", "post-commit"'

        if self._auto_commit_mode == "pre-commit":
            config_extra["enable_auto_commit"] = True
            self._bg_commit_interval_ms = loop_interval_ms
        else:
            config_extra["enable_auto_commit"] = False
            self._bg_commit_interval_ms = config.pop("auto_commit_interval_ms", 5000)

        self._next_wake_at = (
            time.monotonic()
            + min(self._loop_interval_ms, self._bg_commit_interval_ms) / 1000.0
        )

        self._main_loop: Task[typing.Any] = None  # type: ignore[assignment]
        self._rebalance_lock = asyncio.Lock()
        self._shutdown = asyncio.get_running_loop().create_future()
        self._consumer = AIOKafkaConsumer(**config, **config_extra)

    def startup(self) -> Task[typing.Any]:
        def shutdown_log_cb(future: Future[typing.Awaitable[None]]) -> None:
            if future.exception():
                logger.exception(
                    "EVKafkaConsumer has been unexpectedly stopped",
                    exc_info=future.exception(),
                )

        self._main_loop = asyncio.create_task(self.run())
        self._main_loop.add_done_callback(shutdown_log_cb)
        return self._main_loop

    async def run(self) -> None:
        await self._consumer.start()
        self._consumer.subscribe(
            self._topics, listener=RebalanceListener(self.on_rebalance)
        )
        try:
            next_wake_in = min(self._loop_interval_ms, self._bg_commit_interval_ms)
            while not self._shutdown.done():
                tp_messages = await self._consumer.getmany(
                    timeout_ms=next_wake_in, max_records=self._batch_max_size
                )
                if tp_messages:
                    messages = list(chain.from_iterable(tp_messages.values()))
                    async with self._rebalance_lock:
                        await self.process_messages(messages)
                next_wake_in = await self._bg_tasks()

        except ConsumerStoppedError:
            pass
        finally:
            await self._commit()
            await self._consumer.stop()

    async def process_messages(self, messages: list[ConsumerRecord]) -> None:
        for message in messages:
            m_ctx = MessageCtx(
                key=message.key,
                value=message.value,
                headers=tuple(message.headers),
                event_type=None,
            )
            c_ctx = ConsumerCtx(
                group_id=self._group_id,
                client_id=self._client_id,
                topic=message.topic,
                partition=message.partition,
                offset=message.partition,
                timestamp=message.timestamp,
            )
            await self._messages_cb(m_ctx, c_ctx)
            await self._store_post_commit_offset(message)

    async def _bg_tasks(self) -> int:
        if self._auto_commit_mode == "pre-commit":
            return self._loop_interval_ms

        # TODO maybe call _commit and calc next wake time
        return self._loop_interval_ms

    async def on_rebalance(self) -> None:
        async with self._rebalance_lock:
            pass
        await self._commit()

    async def _store_post_commit_offset(self, message: ConsumerRecord) -> None:
        if self._auto_commit_mode == "pre-commit":
            return

        # TODO store locally

    async def _commit(self) -> None:
        if self._auto_commit_mode == "pre-commit":
            return

        # TODO send stored commits

    async def shutdown(self) -> None:
        if self._shutdown.done():
            return  # pragma: no cover
        self._shutdown.set_result(None)
        await asyncio.wait([self._main_loop])
