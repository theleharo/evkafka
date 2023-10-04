import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Any, Awaitable, Callable, Mapping, Type, cast, get_origin

from .context import Context, Request
from .types import F
from .utils import exec_endpoint

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
        self.endpoint_dependencies = get_dependencies(endpoint)
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
                # should not be here
                raise AssertionError("Unexpected typing")

            return await exec_endpoint(func=endpoint, values=sig)

        return app

    def match(self, context: Context) -> bool:
        if self.event_name is None:
            return True

        return context.message.message_type == self.event_name

    async def __call__(self, context: Context) -> None:
        if not self.match(context):
            return

        request = Request(context)
        await self.app(request)


def get_dependencies(endpoint: F) -> EndpointDependencies:
    sig = inspect.signature(endpoint)

    annotations = {}
    for param in sig.parameters.values():
        annotations[param.name] = param.annotation

    assert (
        len(annotations) == 1
    ), "Only one endpoint argument is supported at the moment"

    param_name, param_type = annotations.popitem()

    assert (
        param_type is not inspect.Signature.empty
    ), f'Untyped parameter "{param_name}" for endpoint "{endpoint.__name__}"'

    if get_origin(param_type) is dict:
        param_type = dict

    if param_type is not dict:
        if BaseModel is None or not issubclass(param_type, BaseModel):
            raise AssertionError(
                f"Unsupported parameter type for argument {param_name}"
            )

    return EndpointDependencies(
        payload_param_name=param_name, payload_param_type=param_type
    )
