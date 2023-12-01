import pytest

from evkafka import EVKafkaProducer
from evkafka.sender import Sender, Source


async def test_event_raises_if_producer_exists(mocker):
    producer = mocker.Mock(spec=EVKafkaProducer)
    sender = Sender()
    sender.add_producer_callback(producer)

    with pytest.raises(RuntimeError):
        sender.event("Test")


async def test_sender_calls_source_send(mocker):
    mock_send = mocker.patch("evkafka.sender.Source.send")

    sender = Sender()

    @sender.event("Test")
    async def orig_send(e: dict) -> None:  # noqa: ARG001
        pytest.fail("should not be called")

    await orig_send({"a": "b"})
    mock_send.assert_awaited_once_with({"a": "b"})


async def test_sender_calls_producer_send(mocker):
    producer = mocker.Mock(spec=EVKafkaProducer)

    sender = Sender()

    @sender.event("Test", topic="topic")
    async def orig_send(e: dict) -> None:  # noqa: ARG001
        pytest.fail("should not be called")

    sender.add_producer_callback(producer)

    await orig_send(e={"a": "b"})
    producer.send_event.assert_awaited_once_with(
        event={"a": "b"},
        event_type="Test",
        topic="topic",
    )


async def test_source_send_event_with_args(mocker):
    send_cb = mocker.AsyncMock()
    s = Source(event_type="et", endpoint=mocker.Mock(), send_cb=send_cb, topic="t")

    await s.send({"a": "b"})

    send_cb.assert_awaited_once_with(event={"a": "b"}, event_type="et", topic="t")


async def test_source_send_event_with_kwargs(mocker):
    send_cb = mocker.AsyncMock()
    s = Source(event_type="et", endpoint=mocker.Mock(), send_cb=send_cb, topic="t")

    await s.send(e={"a": "b"})

    send_cb.assert_awaited_once_with(event={"a": "b"}, event_type="et", topic="t")


async def test_source_send_event_call_without_args_raises(mocker):
    send_cb = mocker.AsyncMock()
    s = Source(
        event_type="et",
        endpoint=mocker.MagicMock(__name__="name"),
        send_cb=send_cb,
        topic="t",
    )

    with pytest.raises(TypeError):
        await s.send()
