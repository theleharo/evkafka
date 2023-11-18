import asyncio
import json
from types import TracebackType
from typing import Any, Type

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from evkafka.config import ProducerConfig


class EVKafkaProducer:
    def __init__(self, config: ProducerConfig) -> None:
        config = config.copy()
        self.topic: str | None = config.pop("topic", None)
        self._producer = AIOKafkaProducer(**config)

    async def start(self) -> None:
        await self._producer.start()

    async def flush(self) -> None:
        await self._producer.flush()

    async def stop(self) -> None:
        await self._producer.stop()

    async def send_event(
        self,
        event: Any,
        event_type: str,
        topic: str | None = None,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, bytes] | None = None,
    ) -> asyncio.Future:
        if headers is None:
            headers = {}
        topic = topic or self.topic
        if topic is None:
            raise RuntimeError(
                "No default topic provided for producer.\n"
                "You must specify topic either with send_event() call or with producer config."
            )
        event_headers: dict[str, bytes] = {
            **headers,
            "Event-Type": event_type.encode(),
        }
        value = self.encode_event(event)
        return await self._producer.send(
            topic=topic,
            value=value,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=list(event_headers.items()),
        )

    @staticmethod
    def encode_event(event: Any) -> bytes:
        if isinstance(event, dict):
            value: bytes = json.dumps(event).encode()
        elif isinstance(event, BaseModel):  # type: ignore[truthy-function]
            value = event.model_dump_json().encode()
        elif isinstance(event, str):
            value = event.encode()
        elif isinstance(event, bytes):
            value = event
        else:
            raise RuntimeError("Unexpected event type")

        return value

    async def __aenter__(self) -> "EVKafkaProducer":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()
