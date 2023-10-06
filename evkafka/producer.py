import asyncio
from types import TracebackType
from typing import Type

from aiokafka import AIOKafkaProducer

from evkafka.config import ProducerConfig


class EVKafkaProducer:
    def __init__(self, config: ProducerConfig) -> None:
        self._producer = AIOKafkaProducer(**config)

    async def start(self) -> None:
        await self._producer.start()

    async def flush(self) -> None:
        await self._producer.flush()

    async def stop(self) -> None:
        await self._producer.stop()

    async def send_event(
        self,
        topic: str,
        event: bytes,
        event_name: str,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, bytes] | None = None,
    ) -> asyncio.Future:
        if headers is None:
            headers = {}

        event_headers: dict[str, bytes] = {
            **headers,
            "Event-Type": event_name.encode(),
        }

        return await self._producer.send(
            topic=topic,
            value=event,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=list(event_headers.items()),
        )

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
