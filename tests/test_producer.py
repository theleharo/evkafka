import pytest
from aiokafka import AIOKafkaProducer

from evkafka import EVKafkaProducer


@pytest.fixture
def orig_kafka(mocker):
    kafka = mocker.patch("evkafka.producer.AIOKafkaProducer", spec=AIOKafkaProducer)
    return kafka.return_value


@pytest.fixture
def producer():
    return EVKafkaProducer(config={"bootstrap_servers": "kafka"})


async def test_start(orig_kafka, producer):
    await producer.start()

    orig_kafka.start.assert_awaited_once()


async def test_stop(orig_kafka, producer):
    await producer.stop()

    orig_kafka.stop.assert_awaited_once()


async def test_flush(orig_kafka, producer):
    await producer.flush()

    orig_kafka.flush.assert_awaited_once()


async def test_cm(orig_kafka, producer):
    async with producer as producer:
        pass

    orig_kafka.start.assert_awaited_once()
    orig_kafka.stop.assert_awaited_once()


@pytest.mark.parametrize(
    "headers, exp_headers",
    [
        ({"Header": b"value"}, [("Header", b"value"), ("Event-Type", b"Test")]),
        ({}, [("Event-Type", b"Test")]),
        (None, [("Event-Type", b"Test")]),
        ({"Event-Type": b"other-type"}, [("Event-Type", b"Test")]),
    ],
)
async def test_send_event(orig_kafka, producer, headers, exp_headers):
    res = await producer.send_event(
        topic="topic",
        event=b"{}",
        event_name="Test",
        key=b"key",
        partition=0,
        timestamp_ms=1,
        headers=headers,
    )

    orig_kafka.send.assert_awaited_once_with(
        topic="topic",
        value=b"{}",
        key=b"key",
        partition=0,
        timestamp_ms=1,
        headers=exp_headers,
    )

    assert res == orig_kafka.send.return_value
