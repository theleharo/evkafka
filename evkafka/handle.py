import asyncio
import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Any, Awaitable, Callable, Mapping, Type, cast

from .context import Context, Request
from .types import F

try:
    from pydantic import BaseModel  # type: ignore
except ModuleNotFoundError:
    BaseModel: Type = None  # type: ignore


@dataclass
class EndpointDependencies:
    payload_param_name: str
    payload_param_type: Any


class Handle:
    def __init__(self, event_name: str | None, endpoint: F) -> None:
        self.event_name = event_name
        self.endpoint = endpoint

        sig = inspect.signature(endpoint)

        annotations = {}
        for param in sig.parameters.values():
            annotations[param.name] = param.annotation

        assert (
            len(annotations) == 1
        ), "Only one endpoint argument is supported at the moment"

        param_name, param_type = annotations.popitem()

        if param_type is inspect.Signature.empty:
            raise RuntimeError(
                f'Untyped parameter "{param_name}" for endpoint "{endpoint.__name__}"'
            )

        self.endpoint_dependencies = EndpointDependencies(
            payload_param_name=param_name, payload_param_type=param_type
        )

        self.app = self.get_app()

    def get_app(self) -> Callable[..., Awaitable[None]]:
        @wraps(self.endpoint)
        async def app(
            request: Request,
            endpoint: Callable[..., Any] = self.endpoint,
            endpoint_deps: EndpointDependencies = self.endpoint_dependencies,
        ) -> None:
            sig: dict[str, Any] = {}
            type_ = cast(type, endpoint_deps.payload_param_type)
            origin = getattr(type_, "__origin__", None)

            value = await request.json()

            assert isinstance(value, dict), "Unexpected message format"

            if type_ is dict or origin and issubclass(origin, Mapping):
                sig[endpoint_deps.payload_param_name] = value
            elif BaseModel and issubclass(type_, BaseModel):
                sig[endpoint_deps.payload_param_name] = type_(**value)
            else:
                raise AssertionError("Unexpected typing")

            return await self._exec_endpoint(func=endpoint, values=sig)

        return app

    @staticmethod
    async def _exec_endpoint(func: Callable[..., Any], values: dict[str, Any]) -> Any:
        if inspect.iscoroutinefunction(func):
            return await func(**values)

        return await asyncio.to_thread(func, **values)

    def match(self, context: Context) -> bool:
        if self.event_name is None:
            return True

        return context.message.message_type == self.event_name

    async def __call__(self, context: Context) -> None:
        if not self.match(context):
            return

        request = Request(context)
        await self.app(request)
