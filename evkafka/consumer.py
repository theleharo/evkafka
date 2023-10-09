import asyncio
import logging
import typing
from asyncio import Future, Task
from itertools import chain

from aiokafka import AIOKafkaConsumer, ConsumerStoppedError  # type: ignore

from evkafka.config import ConsumerConfig
from evkafka.context import ConsumerCtx, MessageCtx

logger = logging.getLogger(__name__)


class EVKafkaConsumer:
    def __init__(
        self,
        config: ConsumerConfig,
        messages_cb: typing.Callable[[MessageCtx, ConsumerCtx], typing.Awaitable[None]],
        batch_timeout_ms: int = 1000,
        batch_max_size: int = 1,
    ) -> None:
        config = config.copy()
        self._topics = config.pop("topics")
        self._group_id = config.get("group_id")
        if config.get("client_id", None) is None:
            config["client_id"] = "evkafka"
        self._client_id = config["client_id"]
        self._messages_cb = messages_cb
        self._batch_timeout_ms = batch_timeout_ms  # shutdown response time
        self._batch_max_size = batch_max_size

        self._consumer = AIOKafkaConsumer(**config)
        self._shutdown = asyncio.get_running_loop().create_future()
        self._main_loop: Task[typing.Any] = None  # type: ignore[assignment]

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
        self._consumer.subscribe(self._topics)  # add rebalance listener
        try:
            while not self._shutdown.done():
                messages = await self._consumer.getmany(
                    timeout_ms=self._batch_timeout_ms, max_records=self._batch_max_size
                )
                if messages:
                    for message in chain.from_iterable(messages.values()):
                        m_ctx = MessageCtx(
                            key=message.key,
                            value=message.value,
                            headers=message.headers,
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
        except ConsumerStoppedError:
            pass
        finally:
            await self._consumer.stop()

    async def shutdown(self) -> None:
        if self._shutdown.done():
            return  # pragma: no cover
        self._shutdown.set_result(None)
        await asyncio.wait([self._main_loop])
