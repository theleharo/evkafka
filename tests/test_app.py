import asyncio
import signal
from contextlib import asynccontextmanager

import pytest

from evkafka import EVKafkaApp, EVKafkaProducer, Handler, Request
from evkafka.sender import Sender
from evkafka.state import State
from tests.utils import TestConsumer


@pytest.fixture()
def mocked_consumer(mocker):
    c = mocker.patch("evkafka.app.EVKafkaConsumer")

    inst = set()

    def make_consumer(**kwargs):
        nonlocal inst
        consumer = TestConsumer(**kwargs)
        inst.add(consumer)
        return consumer

    c.side_effect = make_consumer
    return inst


@pytest.fixture()
def producer_cls(mocker):
    return mocker.patch("evkafka.app.EVKafkaProducer", spec=EVKafkaProducer)


@pytest.fixture()
def asyncapi_server(mocker):
    server_cls = mocker.patch("evkafka.app.AsyncApiServer")
    server = server_cls.return_value

    server.start = mocker.AsyncMock()
    server.stop = mocker.AsyncMock()
    return server_cls


@asynccontextmanager
async def run_app(app):
    t = asyncio.create_task(app.serve())
    while not app.started:
        await asyncio.sleep(0.001)

    yield

    app.handle_exit(signal.SIGTERM, None)
    await asyncio.gather(t)


@pytest.mark.usefixtures("mocked_consumer")
async def test_default_consumer_is_added_to_configs():
    app = EVKafkaApp(config={"some": "conf"}, name="some")

    @app.event("EventType")
    def handler(e: dict):  # noqa: ARG001
        pass

    async with run_app(app):
        configs = app.consumer_configs
        assert "some" in configs


async def test_default_consumer_handles_event(mocked_consumer, ctx, decoded_value):
    value = None
    app = EVKafkaApp(config={"some": "conf"})

    @app.event("EventType")
    def handler(e: dict):
        nonlocal value
        value = e

    async with run_app(app):
        consumer: TestConsumer = mocked_consumer.pop()
        await consumer.messages_cb(ctx.message, ctx.consumer)

        assert consumer.config == {"some": "conf"}
        assert value == decoded_value


async def test_added_consumer_handles_event(mocked_consumer, ctx, decoded_value):
    value = None
    app = EVKafkaApp()
    h = Handler()

    @h.event("EventType")
    def handler(e: dict):
        nonlocal value
        value = e

    app.add_consumer(config={"some": "conf"}, handler=h)

    async with run_app(app):
        consumer: TestConsumer = mocked_consumer.pop()
        await consumer.messages_cb(ctx.message, ctx.consumer)
        assert value == decoded_value


@pytest.mark.usefixtures("mocked_consumer")
async def test_consumer_cannot_be_added_after_start():
    app = EVKafkaApp()
    h = Handler()

    @h.event("EventType")
    def handler(e: dict):  # noqa: ARG001
        pass

    app.add_consumer(config={"some": "conf"}, handler=h)

    async with run_app(app):
        with pytest.raises(RuntimeError):
            app.add_consumer(config={"some": "conf"}, handler=h)


async def test_app_exits_on_any_consumer_error(mocked_consumer):
    app = EVKafkaApp()

    h = Handler()

    @h.event("EventType")
    def handler(e: dict):  # noqa: ARG001
        pass

    app.add_consumer(config={"some": "conf"}, handler=h)
    app.add_consumer(config={"some": "conf"}, handler=h)

    t = asyncio.create_task(app.serve())
    while not app.started:
        await asyncio.sleep(0.001)

    consumer: TestConsumer = mocked_consumer.pop()
    consumer.error = True

    await asyncio.gather(t)


async def test_app_lifespan_startup_shutdown():
    started = False
    stopped = False

    @asynccontextmanager
    async def lifespan():
        nonlocal started, stopped
        started = True
        yield
        stopped = True

    app = EVKafkaApp(lifespan=lifespan)

    async with run_app(app):
        assert started
        assert app.started
        assert not stopped

    assert started
    assert stopped


async def test_app_lifespan_broken_startup():
    @asynccontextmanager
    async def lifespan():
        raise Exception
        yield

    app = EVKafkaApp(lifespan=lifespan)

    t = asyncio.create_task(app.serve())
    await asyncio.gather(t)

    assert not app.started
    assert app.should_exit


async def test_app_lifespan_skips_shutdown_on_forced_exit():
    started = False
    stopped = False

    @asynccontextmanager
    async def lifespan():
        nonlocal started, stopped
        started = True
        yield
        stopped = True

    app = EVKafkaApp(lifespan=lifespan)

    async with run_app(app):
        app.handle_exit(signal.SIGINT, None)
        app.handle_exit(signal.SIGINT, None)

    assert started
    assert not stopped


async def test_handler_got_state(mocked_consumer, ctx):
    @asynccontextmanager
    async def lifespan():
        yield {"life": "span"}

    state = None
    app = EVKafkaApp(config={"some": "conf"}, lifespan=lifespan)

    @app.event("EventType")
    def handler(e: dict, r: Request):  # noqa: ARG001
        nonlocal state
        state = r.state

    async with run_app(app):
        consumer: TestConsumer = mocked_consumer.pop()
        await consumer.messages_cb(ctx.message, ctx.consumer)
        assert state == State({"life": "span"})


def test_handle_exit_forces_on_second_call():
    app = EVKafkaApp()
    app.handle_exit(signal.SIGINT, None)
    app.handle_exit(signal.SIGINT, None)

    assert app.force_exit


async def test_app_asyncapi_exposition(asyncapi_server):
    app = EVKafkaApp(expose_asyncapi=True)

    async with run_app(app):
        asyncapi_server.assert_called_once_with(
            '{"asyncapi":"2.6.0","info":{"title":"EVKafka","version":"0.1.0"},"servers":{},"channels":{},"components":{"messages":{}}}',
            host="0.0.0.0",
            port=8080,
        )
        asyncapi_server.return_value.start.assert_awaited_once()

    asyncapi_server.return_value.stop.assert_awaited_once()


async def test_added_producer_starts_and_stops(mocker, producer_cls):
    sender = Sender()

    @sender.event("Event")
    async def send(e: dict):  # noqa: ARG001
        pass

    app = EVKafkaApp()
    config = mocker.Mock()
    app.add_producer(config=config, sender=sender)

    async with run_app(app):
        producer_cls.assert_called_once_with(config=config)
        assert sender.producer == producer_cls.return_value
        producer_cls.return_value.start.assert_awaited_once()
        producer_cls.return_value.stop.assert_not_awaited()

    producer_cls.return_value.stop.assert_awaited_once()


@pytest.mark.usefixtures("producer_cls")
async def test_producer_cannot_be_added_after_start(mocker):
    sender = Sender()

    @sender.event("Event")
    async def send(e: dict):  # noqa: ARG001
        pass

    app = EVKafkaApp()
    app.add_producer(config=mocker.Mock(), sender=sender, name="ok")

    async with run_app(app):
        with pytest.raises(RuntimeError, match="add another producer"):
            app.add_producer(config=mocker.Mock(), sender=mocker.Mock(), name="bad")

    assert "ok" in app.producer_configs
    assert "bad" not in app.producer_configs
