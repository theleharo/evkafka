import pytest

from evkafka.context import ConsumerCtx, Context, MessageCtx


@pytest.fixture()
def raw_value():
    return b'{"a":"b"}'


@pytest.fixture()
def decoded_value():
    return {"a": "b"}


@pytest.fixture()
def ctx(raw_value):
    return Context(
        message=MessageCtx(
            key=b"key",
            value=raw_value,
            headers=(("Event-Type", b"EventType"),),
            event_type="test",
        ),
        consumer=ConsumerCtx(
            group_id="group",
            client_id="client",
            topic="topic",
            partition=1,
            offset=2,
            timestamp=3,
        ),
        state={"some": "state"},
    )


@pytest.fixture()
def req(mocker, decoded_value):
    r = mocker.Mock()
    r.value = b"a"
    r.json = mocker.AsyncMock(return_value=decoded_value)
    return r
