import inspect
from dataclasses import dataclass
from typing import Any, Type, get_origin

from .context import Request
from .types import F

try:
    from pydantic import BaseModel  # type: ignore
except ModuleNotFoundError:
    BaseModel: Type = None  # type: ignore


@dataclass
class EndpointDependencies:
    payload_param_name: str
    payload_param_type: Any
    request_param_name: str | None


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
