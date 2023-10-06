from dataclasses import dataclass, field
from typing import Any

from .state import State
from .utils import load_json


@dataclass
class MessageCtx:
    key: bytes | None
    value: Any
    headers: tuple[tuple[str, bytes], ...]
    event_type: str | None


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

    @property
    def json(self) -> dict[Any, Any]:
        if not hasattr(self, "_json"):
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
