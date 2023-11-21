from functools import wraps
from typing import Any, Awaitable, Callable, cast

from pydantic import BaseModel

from .context import Context, Request
from .dependencies import EndpointDependencies, get_dependencies
from .types import F
from .utils import exec_endpoint


class Handle:
    def __init__(
        self,
        event_type: str,
        endpoint: F,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        self.event_type = event_type
        self.endpoint = endpoint
        self.endpoint_dependencies = get_dependencies(endpoint)
        self.summary = summary
        self.description = description
        self.tags = tags
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
                value: Any = await request.json()
            elif BaseModel and issubclass(type_, BaseModel):  # type: ignore[truthy-function]
                value = type_(**(await request.json()))
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
        return context.message.event_type == self.event_type

    async def __call__(self, context: Context) -> None:
        if not self.match(context):
            return

        request = Request(context)
        await self.app(request)
