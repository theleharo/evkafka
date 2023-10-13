from unittest import mock

import pytest

from evkafka import EVKafkaApp, Handler, TestClient
from evkafka.context import ConsumerCtx, Context, MessageCtx, Request


@pytest.fixture
def send_event():
    return {
        "name": "default",
        "topic": "topic",
        "event": b'{"a":"b"}',
        "event_type": "Event",
        "key": b"key",
        "partition": 1,
        "timestamp_ms": 1000,
        "headers": {"Header": b"Value"},
    }


@pytest.fixture
def exp_ctx(send_event):
    return Context(
        message=MessageCtx(
            key=send_event["key"],
            value=send_event["event"],
            headers=(
                ("Header", b"Value"),
                ("Event-Type", send_event["event_type"].encode()),
            ),
            event_type="Event",
        ),
        consumer=ConsumerCtx(
            group_id="group",
            client_id="client",
            topic=send_event["topic"],
            partition=send_event["partition"],
            offset=mock.ANY,
            timestamp=send_event["timestamp_ms"],
        ),
        state={},
    )


@pytest.fixture
def default_app(exp_ctx):
    app = EVKafkaApp(
        config={"topics": ["topic"], "group_id": "group", "client_id": "client"},
        name="default",
    )

    event = None
    ctx = None

    @app.event("Event")
    async def handle_event(e: bytes, r: Request) -> None:
        nonlocal event, ctx
        event = e
        ctx = r.context

    yield app

    assert event == exp_ctx.message.value
    assert ctx == exp_ctx


@pytest.fixture
def app(exp_ctx):
    app = EVKafkaApp()
    h = Handler()

    event = None
    ctx = None

    @h.event("Event")
    async def handle_event(e: bytes, r: Request) -> None:
        nonlocal event, ctx
        event = e
        ctx = r.context

    app.add_consumer(
        config={"topics": ["topic"], "group_id": "group", "client_id": "client"},
        handler=h,
        name="default",
    )

    yield app

    assert event == exp_ctx.message.value
    assert ctx == exp_ctx


def test_client():
    app = EVKafkaApp()
    with TestClient(app):
        pass


async def test_client_in_async_mode_raises():
    app = EVKafkaApp()
    with pytest.raises(RuntimeError, match="cannot be used"):
        with TestClient(app):
            pass


def test_client_send_event_default_app(default_app, send_event):
    with TestClient(default_app) as c:
        c.send_event(**send_event)


def test_client_send_event_app(app, send_event):
    with TestClient(app) as c:
        c.send_event(**send_event)


def test_client_send_event_app_to_unknown_consumer(send_event):
    app = EVKafkaApp()
    with pytest.raises(RuntimeError, match="Consumer with name"):
        with TestClient(app) as c:
            c.send_event(**send_event)
