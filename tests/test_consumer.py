import asyncio

import pytest
from aiokafka import ConsumerRecord, ConsumerStoppedError
from aiokafka.structs import TopicPartition

from evkafka.consumer import EVKafkaConsumer
from evkafka.context import ConsumerCtx, MessageCtx


@pytest.fixture
def aio_consumer_cls(mocker):
    return mocker.patch("evkafka.consumer.AIOKafkaConsumer")


@pytest.fixture
def aio_consumer(mocker, aio_consumer_cls):
    consumer = aio_consumer_cls.return_value

    consumer.stop = mocker.AsyncMock()
    consumer.start = mocker.AsyncMock()
    consumer.getmany = mocker.AsyncMock()

    return consumer


@pytest.fixture
def config():
    return {
        "bootstrap_servers": "kafka:9092",
        "topics": ["topic"],
        "client_id": "client_id",
    }


@pytest.fixture
def record():
    return ConsumerRecord(
        topic="topic",
        partition=1,
        offset=2,
        timestamp=100,
        timestamp_type=0,
        key=b"key",
        value=b"value",
        checksum=0,
        serialized_key_size=3,
        serialized_value_size=5,
        headers=(("Header", b"Value"),),
    )


@pytest.fixture
def messages_cb(mocker):
    return mocker.AsyncMock()


async def test_consumer_excludes_topics_from_config(
    aio_consumer_cls, config, messages_cb
):
    EVKafkaConsumer(config=config, messages_cb=messages_cb)
    config.pop("topics")
    aio_consumer_cls.assert_called_once_with(**config)


async def test_consumer_sets_client_id_if_not_supplied(
    aio_consumer_cls, config, messages_cb
):
    config.pop("client_id")
    EVKafkaConsumer(config=config, messages_cb=messages_cb)
    config.pop("topics")
    aio_consumer_cls.assert_called_once_with(**{**config, "client_id": "evkafka"})


async def test_consumer_starts_and_stops(aio_consumer, config, messages_cb):
    c = EVKafkaConsumer(config=config, messages_cb=messages_cb)

    c.startup()
    await c.shutdown()

    aio_consumer.start.assert_awaited_once()
    aio_consumer.subscribe.assert_called_once_with(["topic"])
    aio_consumer.stop.assert_awaited_once()


async def test_consumer_propagates_handling_exception(
    aio_consumer, config, messages_cb, record
):
    aio_consumer.getmany.return_value = {
        TopicPartition(partition=record.partition, topic=record.topic): [record]
    }
    messages_cb.side_effect = TypeError
    c = EVKafkaConsumer(config=config, messages_cb=messages_cb)

    t = c.startup()
    done, _ = await asyncio.wait([t])

    task_result = done.pop()
    assert task_result.exception().__class__ == TypeError
    aio_consumer.stop.assert_awaited_once()


async def test_consumer_calls_handler_for_messages(
    aio_consumer, config, messages_cb, record
):
    aio_consumer.getmany.side_effect = [
        {TopicPartition(partition=record.partition, topic=record.topic): [record]},
        ConsumerStoppedError,
    ]
    c = EVKafkaConsumer(config=config, messages_cb=messages_cb)

    t = c.startup()
    done, _ = await asyncio.wait([t])

    messages_cb.assert_awaited_once_with(
        MessageCtx(
            key=b"key", value=b"value", headers=(("Header", b"Value"),), event_type=None
        ),
        ConsumerCtx(
            group_id=None,
            client_id="client_id",
            topic="topic",
            partition=1,
            offset=1,
            timestamp=100,
        ),
    )
