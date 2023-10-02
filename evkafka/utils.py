import json.decoder
from typing import Any

from evkafka.exceptions import UndecodedMessageError


def load_json(value: bytes) -> dict[Any, Any] | list[Any]:
    try:
        return json.loads(value)
    except json.decoder.JSONDecodeError as exc:
        raise UndecodedMessageError from exc
