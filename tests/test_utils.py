import pytest

from evkafka.exceptions import UnsupportedValueError
from evkafka.utils import exec_endpoint, load_json


async def test_exec_endpoint(mocker):
    aio = mocker.patch("evkafka.utils.asyncio")
    aio.to_thread = mocker.AsyncMock()
    func = mocker.Mock()

    await exec_endpoint(func, {"a": "b"})

    aio.to_thread.assert_awaited_once_with(func, a="b")


def test_load_json():
    j = b'{"a":"b"}'

    assert load_json(j) == {"a": "b"}


def test_load_json_bad_json():
    with pytest.raises(UnsupportedValueError, match="Cannot load"):
        load_json(b"not json")


def test_load_json_not_dict():
    with pytest.raises(UnsupportedValueError, match="not a dict"):
        load_json(b"[]")
