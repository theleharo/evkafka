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
from aiokafka.structs import TopicPartition

from evkafka.config import ConsumerConfig, TopicConfig
from evkafka.context import ConsumerCtx, MessageCtx

logger = logging.getLogger(__name__)


class RebalanceListener(ConsumerRebalanceListener):
    def __init__(
        self, on_rebalance_cb: typing.Callable[[], typing.Awaitable[None]]
    ) -> None:
        self.on_rebalance_cb = on_rebalance_cb

    async def on_partitions_revoked(
        self, revoked: list[TopicPartition]  # noqa: ARG002
    ) -> None:
        await self.on_rebalance_cb()

    async def on_partitions_assigned(
        self, assigned: list[TopicPartition]
    ) -> None:  # pragma: no cover
        pass


class EVKafkaConsumer:
    def __init__(
        self,
        config: ConsumerConfig,
        messages_cb: typing.Callable[[MessageCtx, ConsumerCtx], typing.Awaitable[None]],
        loop_interval_ms: int = 1000,
        batch_max_size: int = 1,
    ) -> None:
        self._messages_cb = messages_cb
        self._loop_interval_ms = loop_interval_ms
        self._batch_max_size = batch_max_size

        config = config.copy()
        config.pop("cluster_name", None)
        config.pop("cluster_description", None)
        config_extra: dict[str, typing.Any] = {}
        topics: list[str] | list[TopicConfig] = config.pop("topics")
        assert topics, "Topics list cannot be empty"

        topic_names = []

        for topic in topics:
            if isinstance(topic, str):
                topic_names.append(topic)
            else:
                topic_names.append(typing.cast(TopicConfig, topic)["name"])

        self._topics = topic_names

        self._group_id = config.get("group_id")
        try:
            self._client_id = config["client_id"]
        except KeyError:
            self._client_id = "evkafka"
            config_extra["client_id"] = self._client_id

        max_endpoint_exec_time_ms = config.pop("max_endpoint_exec_time_ms", 20000)
        config_extra["max_poll_interval_ms"] = max_endpoint_exec_time_ms
        config_extra["rebalance_timeout_ms"] = max_endpoint_exec_time_ms

        self._auto_commit_mode = config.pop("auto_commit_mode", "post-commit")
        assert self._auto_commit_mode in [
            "pre-commit",
            "post-commit",
        ], 'Unsupported auto commit mode. Supported modes are: "pre-commit", "post-commit"'

        if self._auto_commit_mode == "pre-commit":
            config_extra["enable_auto_commit"] = True
            self._bg_commit_interval = loop_interval_ms / 1000
        else:
            config_extra["enable_auto_commit"] = False
            self._bg_commit_interval = (
                config.pop("auto_commit_interval_ms", 5000) / 1000
            )
        self._next_commit_at = time.monotonic() + self._bg_commit_interval

        self._main_loop: Task[typing.Any] = None  # type: ignore[assignment]
        self._rebalance_lock = asyncio.Lock()
        self._shutdown = asyncio.get_running_loop().create_future()
        self._consumer = AIOKafkaConsumer(**config, **config_extra)
        self._stored_offsets: dict[TopicPartition, int] = {}

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
            next_wake_in = await self.run_bg_commit()
            while not self._shutdown.done():
                tp_messages = await self._consumer.getmany(
                    timeout_ms=next_wake_in, max_records=self._batch_max_size
                )
                if tp_messages:
                    async with self._rebalance_lock:
                        messages = list(chain.from_iterable(tp_messages.values()))
                        for message in messages:
                            await self._process_message(message)
                            self._store_offset(message)
                next_wake_in = await self.run_bg_commit()

        except ConsumerStoppedError:
            pass
        finally:
            await self.commit()
            await self._consumer.stop()

    async def _process_message(self, message: ConsumerRecord) -> None:
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

    async def run_bg_commit(self) -> int:
        if self._auto_commit_mode == "pre-commit":
            return self._loop_interval_ms

        now = time.monotonic()
        if now > self._next_commit_at:
            await self.commit()
            self._next_commit_at = now + self._bg_commit_interval

        next_commit_in = max(0, self._next_commit_at - time.monotonic())
        return int(min(next_commit_in * 1000, self._loop_interval_ms))

    async def on_rebalance(self) -> None:
        async with self._rebalance_lock:
            pass
        await self.commit()

    def _store_offset(self, message: ConsumerRecord) -> None:
        if self._auto_commit_mode == "pre-commit":
            return
        topic_partition = TopicPartition(message.topic, message.partition)
        self._stored_offsets[topic_partition] = message.offset + 1

    async def commit(self) -> None:
        if self._auto_commit_mode == "pre-commit":
            return
        if self._stored_offsets:
            logger.debug("Commit %s", self._stored_offsets)
            offsets, self._stored_offsets = self._stored_offsets, {}
            await self._consumer.commit(offsets)

    async def shutdown(self) -> None:
        if self._shutdown.done():
            return  # pragma: no cover
        self._shutdown.set_result(None)
        await asyncio.wait([self._main_loop])
