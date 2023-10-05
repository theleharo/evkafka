import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Any, Awaitable, Callable, Type, cast, get_origin

from .context import Context, Request
from .exceptions import UnsupportedValueError
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
    request_param_name: str | None


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
                raise UnsupportedValueError(
                    "Cannot cast event to {type_.__name__} type"
                )

            sig = {endpoint_deps.payload_param_name: value}

            if endpoint_deps.request_param_name:
                sig[endpoint_deps.request_param_name] = request

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

    payload_param_name = None
    payload_param_type = None
    request_param_name = None

    annotations = {}
    for param in sig.parameters.values():
        annotations[param.name] = param.annotation

    for param_name, param_type in annotations.items():
        assert (
            param_type is not inspect.Signature.empty
        ), f'Untyped parameter "{param_name}" for endpoint "{endpoint.__name__}"'

        if get_origin(param_type) is dict:
            param_type = dict

        if issubclass(param_type, Request):
            assert request_param_name is None, "Only one Request parameter is expected"
            request_param_name = param_name
        else:
            assert payload_param_name is None, "Only one payload parameter is expected"
            if param_type in [dict, str, bytes]:
                pass
            elif BaseModel and issubclass(param_type, BaseModel):
                pass
            else:
                raise AssertionError(
                    f"Unsupported parameter type for argument {param_name}"
                )

            payload_param_name = param_name
            payload_param_type = param_type

    assert payload_param_name, "At least one payload parameter is expected"

    return EndpointDependencies(
        payload_param_name=payload_param_name,
        payload_param_type=payload_param_type,
        request_param_name=request_param_name,
    )
