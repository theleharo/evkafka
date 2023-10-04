from typing import Dict

import pytest

from evkafka import handle
from evkafka.handle import Handle, get_dependencies


@pytest.fixture
def req(mocker):
    r = mocker.Mock()
    r.value = b"a"
    r.json = {"a": "b"}
    return r


@pytest.mark.parametrize(
    "typ, exp", [(dict, dict), (Dict, dict), (str, str), (bytes, bytes)]
)
def test_get_dependencies_payload_param_builtins(typ, exp):
    def ep(e: typ):
        pass

    d = get_dependencies(ep)

    assert d.payload_param_name == "e"
    assert d.payload_param_type is exp


def test_get_dependencies_payload_param_pyd_model(mocker):
    class B:
        pass

    mocker.patch.object(handle, "BaseModel", B)

    def ep(e: B):
        pass

    d = get_dependencies(ep)

    assert d.payload_param_name == "e"
    assert d.payload_param_type is B


def test_get_dependencies_raises_for_extra_arg():
    def ep(e: dict, extra: dict):
        pass

    with pytest.raises(AssertionError, match="Only one"):
        get_dependencies(ep)


def test_get_dependencies_raises_for_untyped_arg():
    def ep(e):
        pass

    with pytest.raises(AssertionError, match="Untyped"):
        get_dependencies(ep)


def test_get_dependencies_raises_for_unsupported_type():
    def ep(e: list):
        pass

    with pytest.raises(AssertionError, match="Unsupported"):
        get_dependencies(ep)


@pytest.mark.parametrize("typ,exp_val", [(str, "a"), (bytes, b"a"), (dict, {"a": "b"})])
async def test_handle_simple_type(typ, exp_val, req):
    async def ep(e: typ):
        return e

    h = Handle("ep", ep)
    assert await h.app(req) == exp_val


async def test_handle_pyd_type(mocker, req):
    class B:
        def __init__(self, **kw):
            self.kw = kw

    mocker.patch.object(handle, "BaseModel", B)

    async def ep(e: B):
        return e

    h = Handle("ep", ep)
    res = await h.app(req)

    assert res.kw == {"a": "b"}
