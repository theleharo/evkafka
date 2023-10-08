from typing import Callable

from .context import Context
from .handle import Handle
from .types import F


class Handler:
    def __init__(self) -> None:
        self.handles: list[Handle] = []
        self._event_names: set[str] = set()

    def _register_handle(self, event_name: str, endpoint: F) -> None:
        if event_name in self._event_names:
            raise AssertionError(
                f'Event handler for event "{event_name}" is already registered'
            )
        handle = Handle(event_name=event_name, endpoint=endpoint)
        self.handles.append(handle)
        self._event_names.add(event_name)

    def event(self, event_name: str) -> Callable[[F], F]:
        def decorator(endpoint: F) -> F:
            self._register_handle(event_name, endpoint)
            return endpoint

        return decorator

    async def __call__(self, context: Context) -> None:
        for handle in self.handles:
            if handle.match(context):
                await handle(context)

    def include_handler(self, handler: "Handler") -> None:
        for handle in handler.handles:
            self._register_handle(handle.event_name, handle.endpoint)
