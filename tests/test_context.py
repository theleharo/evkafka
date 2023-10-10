import pytest

from evkafka.context import Request
from evkafka.state import State


@pytest.fixture
def req(ctx):
    return Request(ctx)


def test_request_headers(req):
    assert req.headers == {"Event-Type": b"EventType"}


def test_request_json(req):
    assert req.json == {"a": "b"}


def test_request_key(req):
    assert req.key == b"key"


def test_request_state(req):
    assert req.state == State({"some": "state"})


def test_request_value(req):
    assert req.value == b'{"a":"b"}'
