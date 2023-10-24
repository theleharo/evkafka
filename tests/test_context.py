import pytest

from evkafka.context import Request
from evkafka.state import State


@pytest.fixture()
def req(ctx):
    return Request(ctx)


def test_request_headers(req):
    assert req.headers == {"Event-Type": b"EventType"}


async def test_request_json_fallback(req):
    assert await req.json() == {"a": "b"}


async def test_request_json_decoded_value_cb(req):
    async def cb():
        return {"c": "d"}

    req.context.message.decoded_value_cb = cb

    assert await req.json() == {"c": "d"}


def test_request_key(req):
    assert req.key == b"key"


def test_request_state(req):
    assert req.state == State({"some": "state"})


def test_request_value(req):
    assert req.value == b'{"a":"b"}'
