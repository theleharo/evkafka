from functools import wraps
from typing import Any, Awaitable, Callable, Type, cast

from .context import Context, Request
from .dependencies import EndpointDependencies, get_dependencies
from .types import F
from .utils import exec_endpoint

try:
    from pydantic import BaseModel  # type: ignore
except ModuleNotFoundError:
    BaseModel: Type = None  # type: ignore


class Handle:
    def __init__(self, event_name: str, endpoint: F) -> None:
        self.event_name = event_name
        self.endpoint = endpoint
        self.endpoint_dependencies = get_dependencies(endpoint)
        self.app = self.get_app()

    def get_app(self) -> Callable[..., Awaitable[None]]:
        @wraps(self.endpoint)
        async def app(
            request: Request,
            endpoint: Callable[..., Any] = self.endpoint,
            endpoint_deps: EndpointDependencies = self.endpoint_dependencies,
        ) -> None:
            type_ = cast(type, endpoint_deps.payload_param_type)

            if type_ is dict:
                value: Any = request.json
            elif BaseModel and issubclass(type_, BaseModel):
                value = type_(**request.json)
            elif type_ is str:
                value = request.value.decode()
            elif type_ is bytes:
                value = request.value
            else:
                # get_dependencies should not allow us to be here
                raise AssertionError("Unexpected typing for payload")

            sig = {endpoint_deps.payload_param_name: value}

            if endpoint_deps.request_param_name:
                sig[endpoint_deps.request_param_name] = request

            return await exec_endpoint(func=endpoint, values=sig)

        return app

    def match(self, context: Context) -> bool:
        return context.message.event_type == self.event_name

    async def __call__(self, context: Context) -> None:
        if not self.match(context):
            return

        request = Request(context)
        await self.app(request)
