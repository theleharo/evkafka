import asyncio
import random
import time
from asyncio import AbstractEventLoop
from types import TracebackType
from typing import Any, Type

from evkafka import EVKafkaApp
from evkafka.context import ConsumerCtx, MessageCtx


class TestClient:
    loop: AbstractEventLoop

    def __init__(self, app: EVKafkaApp) -> None:
        self.app = app

    def __enter__(self) -> "TestClient":
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError(
                "TestClient cannot be used inside asynchronous tests or with asynchronous fixtures."
            )
        policy = asyncio.get_event_loop_policy()
        new_loop = policy.new_event_loop()
        policy.set_event_loop(new_loop)
        self.loop = new_loop
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.loop.close()

    def send_event(
        self,
        name: str,
        topic: str,
        event: bytes,
        event_type: str,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, bytes] | None = None,
    ) -> None:
        consumer_config = self.get_consumer_config(name)

        messages_cb = consumer_config["messages_cb"]
        config = consumer_config["config"]

        event_headers: dict[str, bytes] = {
            **(headers if headers else {}),
            "Event-Type": event_type.encode(),
        }

        message_ctx = MessageCtx(
            key=key,
            value=event,
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
            await messages_cb(message_ctx, consumer_ctx)

        self.loop.run_until_complete(send())

    def get_consumer_config(self, name: str) -> dict[str, Any]:
        try:
            return self.app.collect_consumer_configs()[name]
        except KeyError:
            raise RuntimeError(
                f'Consumer with name "{name}" is not registered'
            ) from None
