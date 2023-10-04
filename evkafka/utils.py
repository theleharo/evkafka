import asyncio
import inspect
import json.decoder
from typing import Any, Callable

from evkafka.exceptions import UnsupportedValueError


def load_json(value: bytes) -> dict[Any, Any]:
    try:
        loaded = json.loads(value)
    except json.decoder.JSONDecodeError as exc:
        raise UnsupportedValueError("Cannot load json from value") from exc

    if not isinstance(loaded, dict):
        raise UnsupportedValueError("Loaded json is not a dict")
    return loaded


async def exec_endpoint(func: Callable[..., Any], values: dict[str, Any]) -> Any:
    if inspect.iscoroutinefunction(func):
        return await func(**values)

    return await asyncio.to_thread(func, **values)
