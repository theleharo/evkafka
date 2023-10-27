from contextlib import asynccontextmanager
from unittest import mock

import pytest

from evkafka import EVKafkaApp, Handler, TestClient
from evkafka.context import ConsumerCtx, Context, MessageCtx, Request


@pytest.fixture()
def send_event():
    return {
        "topic": "topic",
        "event": b'{"a": "b"}',
        "event_type": "Event",
        "key": b"key",
        "partition": 1,
        "timestamp_ms": 1000,
        "headers": {"Header": b"Value"},
    }


@pytest.fixture()
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
            decoded_value_cb=mock.ANY,
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


@pytest.fixture()
def endpoint(mocker):
    return mocker.Mock()


@pytest.fixture()
def default_app(endpoint):
    app = EVKafkaApp(
        config={"topics": ["topic"], "group_id": "group", "client_id": "client"},
    )

    @app.event("Event")
    async def handle_event(e: bytes, r: Request) -> None:  # noqa: ARG001
        endpoint(context=r.context, value=e)

    return app


@pytest.fixture()
def app(endpoint):
    app = EVKafkaApp()
    h = Handler()

    @h.event("Event")
    async def handle_event(e: bytes, r: Request) -> None:  # noqa: ARG001
        endpoint(context=r.context, value=e)

    app.add_consumer(
        config={"topics": ["topic"], "group_id": "group", "client_id": "client"},
        handler=h,
        name="app-consumer",
    )

    return app


@pytest.fixture()
def lifespan(mocker):
    start = mocker.AsyncMock()
    stop = mocker.AsyncMock()

    @asynccontextmanager
    async def lifespan():
        await start()
        yield {"some": "state"}
        await stop()

    return lifespan, start, stop


def test_client_no_consumers(send_event):
    app = EVKafkaApp()
    with pytest.raises(AssertionError, match="No consumers"):
        with TestClient(app) as c:
            c.send_event(**send_event)


async def test_client_in_async_mode_raises():
    app = EVKafkaApp()
    with pytest.raises(AssertionError, match="cannot be used"):
        with TestClient(app):
            pass


def test_client_send_event_default_app(default_app, send_event, endpoint, exp_ctx):
    with TestClient(default_app) as c:
        c.send_event(**send_event)
    endpoint.assert_called_once_with(context=exp_ctx, value=exp_ctx.message.value)


def test_client_send_event_app(app, send_event, endpoint, exp_ctx):
    with TestClient(app) as c:
        c.send_event(**send_event)
    endpoint.assert_called_once_with(context=exp_ctx, value=exp_ctx.message.value)


def test_client_send_event_to_unknown_consumer(send_event):
    app = EVKafkaApp(config={"topics": ["topic"]}, name="default")

    @app.event("Event")
    def handle_event(e: bytes):  # noqa: ARG001
        pass

    with pytest.raises(AssertionError, match="Consumer with name"):
        with TestClient(app) as c:
            c.send_event(**send_event, consumer_name="unknown")


def test_client_send_event_too_many_consumers(send_event):
    h = Handler()

    @h.event("Event")
    async def handle_event(e: bytes):  # noqa: ARG001
        pass

    app = EVKafkaApp()
    app.add_consumer(
        config={"topics": ["topic"], "group_id": "group", "client_id": "client"},
        handler=h,
        name="first-consumer",
    )
    app.add_consumer(
        config={"topics": ["topic"], "group_id": "group", "client_id": "client"},
        handler=h,
        name="second-consumer",
    )

    with pytest.raises(AssertionError, match="Multiple consumers"):
        with TestClient(app) as c:
            c.send_event(**send_event)


def test_client_executes_lifespan(lifespan):
    ls, start, stop = lifespan
    app = EVKafkaApp(lifespan=ls)
    with TestClient(app):
        start.assert_awaited_once()
        stop.assert_not_awaited()
    stop.assert_awaited_once()


def test_client_broken_lifespan_start(lifespan):
    ls, start, stop = lifespan
    start.side_effect = Exception
    app = EVKafkaApp(lifespan=ls)
    with pytest.raises(RuntimeError, match="not started"):
        with TestClient(app):
            pass


def test_client_broken_lifespan_stop(lifespan):
    ls, start, stop = lifespan
    stop.side_effect = Exception
    app = EVKafkaApp(lifespan=ls)
    with pytest.raises(RuntimeError, match="not stopped"):
        with TestClient(app):
            pass


@pytest.mark.parametrize("value", [b'{"a": "b"}', '{"a": "b"}', {"a": "b"}])
def test_client_send_event_types(default_app, endpoint, value):
    with TestClient(default_app) as c:
        c.send_event(event_type="Event", event=value, topic="topic")
    assert endpoint.call_args.kwargs["value"] == b'{"a": "b"}'
