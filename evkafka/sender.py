import asyncio
from typing import Any, Callable, Protocol, cast

from .producer import EVKafkaProducer
from .types import F


class SendEvent(Protocol):
    async def __call__(
        self,
        event: Any,
        event_type: str,
        topic: str | None = None,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, bytes] | None = None,
    ) -> asyncio.Future:  # pragma: no cover
        ...


class Source:
    def __init__(
        self,
        event_type: str,
        endpoint: F,
        send_cb: SendEvent,
        topic: str | None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        # analyze endpoint args: event input
        self.event_type = event_type
        self.endpoint = endpoint
        self.send_cb = send_cb
        self.topic = topic
        self.summary = summary
        self.description = description
        self.tags = tags

    async def send(self, *args: Any, **kwargs: Any) -> None:
        if args:
            event = args[0]
        elif kwargs:
            _, event = kwargs.popitem()
        else:
            raise TypeError(
                f"{self.endpoint.__name__}() missing 1 required positional argument: {{}}"
            )

        await self.send_cb(
            event=event,
            event_type=self.event_type,
            topic=self.topic,
        )


class Sender:
    def __init__(self) -> None:
        self.sources: list[Source] = []
        self.producer: EVKafkaProducer | None = None

    def _register_source(
        self,
        event_type: str,
        endpoint: F,
        topic: str | None,
        summary: str | None,
        description: str | None,
        tags: list[str] | None,
    ) -> F:
        source = Source(
            event_type,
            endpoint,
            self.producer_send_cb,
            topic,
            summary,
            description,
            tags,
        )
        self.sources.append(source)
        return cast(F, source.send)

    def event(
        self,
        event_type: str,
        *,
        topic: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[F], F]:
        if self.producer:
            raise RuntimeError(
                "Cannot register event source after an application has started"
            )

        def decorator(endpoint: F) -> F:
            return self._register_source(
                event_type, endpoint, topic, summary, description, tags
            )

        return decorator

    def add_producer_callback(self, producer: EVKafkaProducer) -> None:
        self.producer = producer

    async def producer_send_cb(
        self,
        event: Any,
        event_type: str,
        topic: str | None = None,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, bytes] | None = None,
    ) -> asyncio.Future:
        assert self.producer

        kwargs = {"event": event, "event_type": event_type}
        if topic:
            kwargs["topic"] = topic
        if key:
            kwargs["key"] = key
        if partition:
            kwargs["partition"] = partition
        if timestamp_ms:
            kwargs["timestamp_ms"] = timestamp_ms
        if headers:
            kwargs["headers"] = headers

        return await self.producer.send_event(**kwargs)
