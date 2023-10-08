import pytest

from evkafka import Handler


@pytest.fixture
def handler():
    return Handler()


@pytest.fixture
def handle(mocker):
    return mocker.patch("evkafka.handler.Handle")


def test_handler_add_event(handler, handle):
    def h(e: dict):
        pass

    handler.event("ev")(h)

    assert len(handler.handles) == 1
    assert handler.handles[0] == handle.return_value
    handle.assert_called_once_with(event_name="ev", endpoint=h)


def test_handler_add_event_with_the_same_name_raises(handler, handle):
    def h(e: dict):
        pass

    handler.event("ev")(h)

    with pytest.raises(AssertionError):
        handler.event("ev")(lambda: None)
    handle.assert_called_once_with(event_name="ev", endpoint=h)


def test_handler_include_handler(handler):
    def ev(e: dict):
        pass

    def ev2(e: dict):
        pass

    handler.event("ev")(ev)
    sub_h = Handler()
    sub_h.event("ev2")(ev2)

    handler.include_handler(sub_h)

    # not the same handle but copy
    assert len(handler.handles) == 2
    assert handler.handles[1].endpoint == sub_h.handles[0].endpoint
    assert handler.handles[1] != sub_h.handles[0]


@pytest.mark.parametrize("name,exp_called", [("test", True), ("ev", False)])
async def test_int_handler_call_matched(ctx, handler, name, exp_called):
    called = False

    @handler.event(name)
    def h(e: dict):
        nonlocal called
        called = True

    await handler(ctx)

    assert called == exp_called
