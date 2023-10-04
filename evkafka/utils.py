import asyncio
import inspect
import json.decoder
from typing import Any, Callable

from evkafka.exceptions import UndecodedMessageError


def load_json(value: bytes) -> dict[Any, Any] | list[Any]:
    try:
        return json.loads(value)
    except json.decoder.JSONDecodeError as exc:
        raise UndecodedMessageError from exc


async def exec_endpoint(func: Callable[..., Any], values: dict[str, Any]) -> Any:
    if inspect.iscoroutinefunction(func):
        return await func(**values)

    return await asyncio.to_thread(func, **values)
