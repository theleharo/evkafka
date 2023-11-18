from typing import Callable

from .context import Context
from .handle import Handle
from .types import F


class Handler:
    def __init__(self) -> None:
        self.handles: list[Handle] = []
        self._event_types: set[str] = set()

    def _register_handle(
        self,
        event_type: str,
        endpoint: F,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        if event_type in self._event_types:
            raise AssertionError(
                f'Event handler for event "{event_type}" is already registered'
            )
        handle = Handle(
            event_type=event_type,
            endpoint=endpoint,
            summary=summary,
            description=description,
            tags=tags,
        )
        self.handles.append(handle)
        self._event_types.add(event_type)

    def event(
        self,
        event_type: str,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[F], F]:
        def decorator(endpoint: F) -> F:
            self._register_handle(event_type, endpoint, summary, description, tags)
            return endpoint

        return decorator

    async def __call__(self, context: Context) -> None:
        for handle in self.handles:
            if handle.match(context):
                await handle(context)

    def include_handler(self, handler: "Handler") -> None:
        for handle in handler.handles:
            self._register_handle(handle.event_type, handle.endpoint)
