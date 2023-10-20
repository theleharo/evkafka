from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from .state import State
from .utils import load_json


@dataclass
class MessageCtx:
    key: bytes | None
    value: bytes
    headers: tuple[tuple[str, bytes], ...]
    event_type: str | None = None
    decoded_value_cb: Callable[[], Awaitable[dict[Any, Any]]] | None = None


@dataclass
class ConsumerCtx:
    group_id: str | None
    client_id: str
    topic: str
    partition: int
    offset: int
    timestamp: int


@dataclass
class Context:
    message: MessageCtx
    consumer: ConsumerCtx
    state: dict


HandlerApp = Callable[[Context], Awaitable[None]]


@dataclass
class AppContext:
    state: dict = field(default_factory=dict)


class Request:
    def __init__(self, context: Context) -> None:
        self.context = context

    @property
    def headers(self) -> dict[str, bytes]:
        if not hasattr(self, "_headers"):
            self._headers = dict(self.context.message.headers)
        return self._headers

    async def json(self) -> dict[Any, Any]:
        if not hasattr(self, "_json"):
            if self.context.message.decoded_value_cb is not None:
                self._json = await self.context.message.decoded_value_cb()
            else:
                # fallback
                self._json = load_json(self.context.message.value)
        return self._json

    @property
    def key(self) -> bytes | None:
        return self.context.message.key

    @property
    def state(self) -> State:
        if not hasattr(self, "_state"):
            self._state = State(self.context.state)
        return self._state

    @property
    def value(self) -> Any:
        return self.context.message.value
