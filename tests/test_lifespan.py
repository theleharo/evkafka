from contextlib import asynccontextmanager

from evkafka.lifespan import LifespanManager


async def test_lifespan_fails_to_start():
    class cm:
        async def __aenter__(self):
            raise Exception

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    lm = LifespanManager(cm)

    await lm.start()
    assert lm.should_exit

    await lm.stop()


async def test_lifespan_state():
    @asynccontextmanager
    async def cm():
        yield {"a": "b"}

    lm = LifespanManager(cm)

    await lm.start()
    assert not lm.should_exit

    assert lm.state == {"a": "b"}

    await lm.stop()
    assert not lm.should_exit


async def test_lifespan_no_state():
    @asynccontextmanager
    async def cm():
        yield

    lm = LifespanManager(cm)

    await lm.start()
    assert not lm.should_exit

    assert lm.state == {}

    await lm.stop()
    assert not lm.should_exit


async def test_lifespan_empty():
    lm = LifespanManager(None)

    await lm.start()
    assert not lm.should_exit

    assert lm.state == {}

    await lm.stop()
    assert not lm.should_exit


async def test_lifespan_fails_at_exit():
    class cm:
        async def __aenter__(self):
            pass

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            raise Exception

    lm = LifespanManager(cm)

    await lm.start()
    assert not lm.should_exit

    await lm.stop()
    assert lm.should_exit
