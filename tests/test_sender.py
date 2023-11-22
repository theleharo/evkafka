import pytest

from evkafka import EVKafkaProducer
from evkafka.sender import Sender


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

    await orig_send({})
    mock_send.assert_awaited_once_with({})


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
