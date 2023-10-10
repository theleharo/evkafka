import pytest

from evkafka import handle
from evkafka.context import Request
from evkafka.dependencies import EndpointDependencies
from evkafka.handle import Handle


@pytest.fixture
def get_deps(mocker):
    return mocker.patch("evkafka.handle.get_dependencies")


@pytest.mark.parametrize("typ,exp_val", [(str, "a"), (bytes, b"a"), (dict, {"a": "b"})])
async def test_handle_event_with_simple_type(typ, exp_val, req, get_deps):
    async def ep(e):
        return e

    get_deps.return_value = EndpointDependencies(
        payload_param_name="e", payload_param_type=typ, request_param_name=None
    )

    h = Handle("ep", ep)
    assert await h.app(req) == exp_val


async def test_handle_event_with_pyd_type(mocker, req, get_deps):
    class B:
        def __init__(self, **kw):
            self.kw = kw

    mocker.patch.object(handle, "BaseModel", B)

    async def ep(e: B):
        return e

    get_deps.return_value = EndpointDependencies(
        payload_param_name="e", payload_param_type=B, request_param_name=None
    )

    h = Handle("ep", ep)
    res = await h.app(req)

    assert res.kw == {"a": "b"}


async def test_handle_event_and_request(req, get_deps):
    async def ep(r: Request, e: str):
        return r, e

    get_deps.return_value = EndpointDependencies(
        payload_param_name="e", payload_param_type=str, request_param_name="r"
    )

    h = Handle("ep", ep)
    assert await h.app(req) == (req, "a")


async def test_handle_event_has_unsupported_type(req, get_deps):
    get_deps.return_value = EndpointDependencies(
        payload_param_name="e", payload_param_type=list, request_param_name=None
    )

    h = Handle("ep", lambda: None)
    with pytest.raises(AssertionError):
        await h.app(req)


@pytest.mark.parametrize(
    "event_type,is_match", [("event", True), ("other", False), (None, False)]
)
def test_match(mocker, event_type, is_match):
    def ep(e: str):
        pass

    h = Handle("event", ep)

    ctx = mocker.Mock()
    ctx.message.event_type = event_type

    assert h.match(ctx) is is_match


@pytest.mark.usefixtures("get_deps")
async def test_handle_unmatched_event_call(mocker):
    h = Handle("event", lambda: None)
    app_mock = mocker.AsyncMock()
    mocker.patch.object(h, "app", app_mock)
    ctx_mock = mocker.Mock()
    ctx_mock.message.event_type = "unknown"

    await h(ctx_mock)

    app_mock.assert_not_awaited()


@pytest.mark.usefixtures("get_deps")
async def test_handle_call(mocker):
    h = Handle("event", lambda: None)
    app_mock = mocker.AsyncMock()
    mocker.patch.object(h, "app", app_mock)
    ctx_mock = mocker.Mock()
    ctx_mock.message.event_type = "event"

    await h(ctx_mock)

    app_mock.assert_awaited_once()
    arg = app_mock.await_args[0][0]
    assert isinstance(arg, Request)
    assert arg.context == ctx_mock
