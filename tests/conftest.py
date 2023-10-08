import pytest

from evkafka.context import ConsumerCtx, Context, MessageCtx


@pytest.fixture
def ctx():
    return Context(
        message=MessageCtx(
            key=b"key",
            value=b'{"a":"b"}',
            headers=(("header", b"value"),),
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
