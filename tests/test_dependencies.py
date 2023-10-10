from typing import Dict

import pytest

from evkafka import dependencies
from evkafka.context import Request
from evkafka.handle import get_dependencies


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

    mocker.patch.object(dependencies, "BaseModel", B)

    def ep(e: B):
        pass

    d = get_dependencies(ep)

    assert d.payload_param_name == "e"
    assert d.payload_param_type is B


def test_get_dependencies_request_arg():
    def ep(e: dict, r: Request):
        pass

    d = get_dependencies(ep)

    assert d.request_param_name == "r"


def test_get_dependencies_raises_for_extra_arg():
    def ep(e: dict, extra: dict):
        pass

    with pytest.raises(AssertionError, match="Only one payload"):
        get_dependencies(ep)


def test_get_dependencies_raises_for_extra_req():
    def ep(e: dict, r: Request, x: Request):
        pass

    with pytest.raises(AssertionError, match="Only one Request"):
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


def test_get_dependencies_raises_for_no_payload_param():
    def ep(r: Request):
        pass

    with pytest.raises(AssertionError, match="At least"):
        get_dependencies(ep)
