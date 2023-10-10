import asyncio
import signal
from contextlib import asynccontextmanager

import pytest

from evkafka import EVKafkaApp, Handler, Request
from evkafka.state import State
from tests.utils import TestConsumer


@pytest.fixture
def test_consumer(mocker):
    c = mocker.patch("evkafka.app.EVKafkaConsumer")

    inst = set()

    def make_consumer(**kwargs):
        nonlocal inst
        consumer = TestConsumer(**kwargs)
        inst.add(consumer)
        return consumer

    c.side_effect = make_consumer
    return inst


@asynccontextmanager
async def run_app(app):
    t = asyncio.create_task(app.serve())
    while not app.started:
        await asyncio.sleep(0.001)

    yield

    app.handle_exit(signal.SIGTERM, None)
    await asyncio.gather(t)


async def test_default_handler_handles_event(test_consumer, ctx, decoded_value):
    value = None
    app = EVKafkaApp(config={"some": "conf"})

    @app.event("EventType")
    def handler(e: dict):
        nonlocal value
        value = e

    async with run_app(app):
        consumer: TestConsumer = test_consumer.pop()
        await consumer.messages_cb(ctx.message, ctx.consumer)

        assert consumer.config == {"some": "conf"}
        assert value == decoded_value


async def test_added_consumer_handles_event(test_consumer, ctx, decoded_value):
    value = None
    app = EVKafkaApp()
    h = Handler()

    @h.event("EventType")
    def handler(e: dict):
        nonlocal value
        value = e

    app.add_consumer(config={"some": "conf"}, handler=h)

    async with run_app(app):
        consumer: TestConsumer = test_consumer.pop()
        await consumer.messages_cb(ctx.message, ctx.consumer)
        assert value == decoded_value


async def test_app_exits_on_any_consumer_error(test_consumer, ctx, decoded_value):
    app = EVKafkaApp()

    h = Handler()

    @h.event("EventType")
    def handler(e: dict):
        pass

    app.add_consumer(config={"some": "conf"}, handler=h)
    app.add_consumer(config={"some": "conf"}, handler=h)

    t = asyncio.create_task(app.serve())
    while not app.started:
        await asyncio.sleep(0.001)

    consumer: TestConsumer = test_consumer.pop()
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


async def test_handler_got_state(test_consumer, ctx, decoded_value):
    @asynccontextmanager
    async def lifespan():
        yield {"life": "span"}

    state = None
    app = EVKafkaApp(config={"some": "conf"}, lifespan=lifespan)

    @app.event("EventType")
    def handler(e: dict, r: Request):
        nonlocal state
        state = r.state

    async with run_app(app):
        consumer: TestConsumer = test_consumer.pop()
        await consumer.messages_cb(ctx.message, ctx.consumer)
        assert state == State({"life": "span"})


def test_handle_exit_forces_on_second_call():
    app = EVKafkaApp()
    app.handle_exit(signal.SIGINT, None)
    app.handle_exit(signal.SIGINT, None)

    assert app.force_exit
