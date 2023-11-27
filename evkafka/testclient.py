import asyncio
import random
import threading
import time
from asyncio import AbstractEventLoop
from types import TracebackType
from typing import Any, Type

from evkafka import EVKafkaApp, EVKafkaProducer
from evkafka.context import AppContext, ConsumerCtx, MessageCtx
from evkafka.lifespan import LifespanManager


class TestClient:
    _loop: AbstractEventLoop
    _lifespan_manager: LifespanManager

    def __init__(self, app: EVKafkaApp) -> None:
        self.app = app

    def send_event(
        self,
        event: Any,
        event_type: str,
        topic: str,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, bytes] | None = None,
        consumer_name: str | None = None,
    ) -> None:
        consumer_config = self.get_consumer_config(consumer_name)
        messages_cb = consumer_config["messages_cb"]
        config = consumer_config["config"]

        event_headers: dict[str, bytes] = {
            **(headers if headers else {}),
            "Event-Type": event_type.encode(),
        }
        value = EVKafkaProducer.encode_event(event)
        message_ctx = MessageCtx(
            key=key,
            value=value,
            headers=tuple(event_headers.items()),
            event_type=event_type,
        )
        consumer_ctx = ConsumerCtx(
            group_id=config.get("group_id"),
            client_id=config.get("client_id"),
            topic=topic,
            partition=partition or 0,
            offset=random.randint(1, 1000000),
            timestamp=timestamp_ms or time.time_ns() // 1000000,
        )

        async def send() -> None:
            app_ctx = AppContext()
            app_ctx.state = self._lifespan_manager.state
            await messages_cb(message_ctx, consumer_ctx, app_context=app_ctx)

        asyncio.run_coroutine_threadsafe(send(), self._loop)

    def get_consumer_config(self, name: str | None) -> dict[str, Any]:
        configs = self.app.consumer_configs
        if len(configs) == 0:
            raise AssertionError("No consumers registered")

        if name is None:
            if len(configs) == 1:
                return list(configs.values())[0]
            raise AssertionError(
                "Multiple consumers registered. You need to provide\n"
                "a consumer name."
            )
        try:
            return configs[name]
        except KeyError:
            raise AssertionError(
                f'Consumer with name "{name}" is not registered'
            ) from None

    def __enter__(self) -> "TestClient":
        self._start_test_loop()
        self._start_lifespan()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            self._stop_lifespan()
        finally:
            self._stop_test_loop()

    def _start_test_loop(self) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise AssertionError(
                "TestClient cannot be used inside asynchronous tests or with asynchronous fixtures."
            )
        self._test_loop_started = threading.Event()
        self._test_loop_thread = threading.Thread(target=self._test_loop)
        self._test_loop_thread.start()
        self._test_loop_started.wait()

    def _start_lifespan(self) -> None:
        self._lifespan_manager = LifespanManager(self.app.lifespan)
        asyncio.run_coroutine_threadsafe(
            self._lifespan_manager.start(), self._loop
        ).result()
        if self._lifespan_manager.should_exit:
            self._stop_test_loop()
            raise RuntimeError("Lifespan has not started properly")

    def _test_loop(self) -> None:
        policy = asyncio.get_event_loop_policy()
        self._loop = policy.new_event_loop()
        policy.set_event_loop(self._loop)
        self._test_loop_started.set()
        try:
            self._loop.run_forever()
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()

    def _stop_lifespan(self) -> None:
        asyncio.run_coroutine_threadsafe(
            self._lifespan_manager.stop(), self._loop
        ).result()
        if self._lifespan_manager.should_exit:
            raise RuntimeError("Lifespan has not stopped properly")

    def _stop_test_loop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._test_loop_thread.join()
