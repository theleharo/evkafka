from typing import Dict

import pytest

from evkafka import handle
from evkafka.handle import get_dependencies


@pytest.mark.parametrize("typ", [dict, Dict])
def test_get_dependencies_payload_param_dict(typ):
    def ep(e: typ):
        pass

    d = get_dependencies(ep)

    assert d.payload_param_name == "e"
    assert d.payload_param_type is dict


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
