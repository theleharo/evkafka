from dataclasses import dataclass
from typing import Any

from .state import State
from .utils import load_json


@dataclass
class MessageCtx:
    key: bytes | None
    value: Any
    headers: tuple[tuple[str, bytes], ...]
    message_type: str | None


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


class Request:
    def __init__(self, context: Context) -> None:
        self._context = context

    @property
    def headers(self) -> dict[str, bytes]:
        if not hasattr(self, "_headers"):
            self._headers = dict(self._context.message.headers)
        return self._headers

    @property
    def json(self) -> dict[Any, Any]:
        if not hasattr(self, "_json"):
            self._json = load_json(self._context.message.value)
        return self._json

    @property
    def key(self) -> bytes | None:
        return self._context.message.key

    @property
    def state(self) -> State:
        if not hasattr(self, "_state"):
            self._state = State(self._context.state)
        return self._state

    @property
    def value(self) -> Any:
        return self._context.message.value
