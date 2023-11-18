import asyncio
import dataclasses
from unittest.mock import call

import pytest
from aiokafka import ConsumerRecord, ConsumerStoppedError
from aiokafka.structs import TopicPartition

from evkafka.consumer import EVKafkaConsumer, RebalanceListener
from evkafka.context import ConsumerCtx, MessageCtx


@pytest.fixture()
def aio_consumer_cls(mocker):
    return mocker.patch("evkafka.consumer.AIOKafkaConsumer")


@pytest.fixture(autouse=True)
def aio_consumer(mocker, aio_consumer_cls):
    consumer = aio_consumer_cls.return_value

    consumer.stop = mocker.AsyncMock()
    consumer.start = mocker.AsyncMock()
    consumer.getmany = mocker.AsyncMock()
    consumer.commit = mocker.AsyncMock()

    return consumer


@pytest.fixture()
def config():
    return {
        "bootstrap_servers": "kafka:9092",
        "topics": ["topic"],
        "client_id": "client_id",
    }


@pytest.fixture()
def config_pre(config):
    return {
        **config,
        "auto_commit_mode": "pre-commit",
    }


@pytest.fixture()
def config_post(config):
    return {
        **config,
        "auto_commit_mode": "post-commit",
    }


@pytest.fixture()
def config_out():
    return {
        "bootstrap_servers": "kafka:9092",
        "client_id": "client_id",
        "max_poll_interval_ms": 20000,
        "rebalance_timeout_ms": 20000,
    }


@pytest.fixture()
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


@pytest.fixture()
def record2(record):
    return dataclasses.replace(record, offset=3, value=b"value2")


@pytest.fixture()
def messages_cb(mocker):
    return mocker.AsyncMock()


@pytest.fixture()
def _getmany_returns_no_data_and_stops(aio_consumer):
    aio_consumer.getmany.side_effect = [
        None,
        ConsumerStoppedError,
    ]


@pytest.fixture()
def _getmany_returns_record_and_stops(aio_consumer, record):
    aio_consumer.getmany.side_effect = [
        {TopicPartition(record.topic, record.partition): [record]},
        ConsumerStoppedError,
    ]


@pytest.fixture()
def commit(mocker):
    return mocker.patch(
        "evkafka.consumer.EVKafkaConsumer.commit", new_callable=mocker.AsyncMock
    )


async def test_consumer_excludes_topics_from_config(
    aio_consumer_cls, config, messages_cb, config_out
):
    EVKafkaConsumer(config=config, messages_cb=messages_cb)
    aio_consumer_cls.assert_called_once_with(**config_out, enable_auto_commit=False)


async def test_consumer_sets_client_id_if_not_supplied(
    aio_consumer_cls, config, messages_cb, config_out
):
    config.pop("client_id")
    EVKafkaConsumer(config=config, messages_cb=messages_cb)
    config_out.pop("client_id")
    aio_consumer_cls.assert_called_once_with(
        **config_out, client_id="evkafka", enable_auto_commit=False
    )


async def test_consumer_sets_pre_commit_mode(
    aio_consumer_cls, config, messages_cb, config_out
):
    EVKafkaConsumer(
        config=dict(**config, auto_commit_mode="pre-commit"), messages_cb=messages_cb
    )

    aio_consumer_cls.assert_called_once_with(**config_out, enable_auto_commit=True)


async def test_consumer_sets_post_commit_mode(
    aio_consumer_cls, config, messages_cb, config_out
):
    EVKafkaConsumer(
        config=dict(**config, auto_commit_mode="post-commit"), messages_cb=messages_cb
    )

    aio_consumer_cls.assert_called_once_with(**config_out, enable_auto_commit=False)


async def test_consumer_starts_and_stops(mocker, aio_consumer, config_pre, messages_cb):
    rebalance_cls = mocker.patch("evkafka.consumer.RebalanceListener")
    c = EVKafkaConsumer(config=config_pre, messages_cb=messages_cb)

    c.startup()
    await c.shutdown()

    aio_consumer.start.assert_awaited_once()
    aio_consumer.subscribe.assert_called_once_with(
        ["topic"], listener=rebalance_cls.return_value
    )
    rebalance_cls.assert_called_once_with(c.on_rebalance)

    aio_consumer.stop.assert_awaited_once()


async def test_consumer_subscribes_with_topicconfig(
    mocker, aio_consumer, config_pre, messages_cb
):
    rebalance_cls = mocker.patch("evkafka.consumer.RebalanceListener")
    config_pre["topics"] = [{"name": "topic1"}]
    c = EVKafkaConsumer(config=config_pre, messages_cb=messages_cb)

    c.startup()
    await c.shutdown()

    aio_consumer.subscribe.assert_called_once_with(
        ["topic1"], listener=rebalance_cls.return_value
    )


@pytest.mark.usefixtures("_getmany_returns_no_data_and_stops")
async def test_consumer_stops_on_consumer_stopped(config_pre, messages_cb):
    c = EVKafkaConsumer(config=config_pre, messages_cb=messages_cb)

    t = c.startup()
    await asyncio.wait([t])  # consumer stops due to _getmany... fixture


@pytest.mark.usefixtures("_getmany_returns_record_and_stops")
async def test_consumer_calls_handler_for_messages(config_pre, messages_cb):
    c = EVKafkaConsumer(config=config_pre, messages_cb=messages_cb)

    t = c.startup()
    await asyncio.wait([t])  # consumer stops due to _getmany... fixture

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


@pytest.mark.usefixtures("_getmany_returns_record_and_stops")
async def test_consumer_propagates_handling_exception(
    aio_consumer, config_pre, messages_cb
):
    messages_cb.side_effect = TypeError
    c = EVKafkaConsumer(config=config_pre, messages_cb=messages_cb)

    t = c.startup()
    done, _ = await asyncio.wait([t])

    task_result = done.pop()
    assert task_result.exception().__class__ == TypeError
    aio_consumer.stop.assert_awaited_once()


@pytest.mark.usefixtures("_getmany_returns_record_and_stops")
async def test_consumer_calls_commit_at_exit(
    aio_consumer, config_post, messages_cb, record
):
    c = EVKafkaConsumer(config=config_post, messages_cb=messages_cb)

    t = c.startup()
    await asyncio.wait([t])

    aio_consumer.commit.assert_awaited_once_with(
        {TopicPartition(record.topic, record.partition): record.offset + 1}
    )


async def test_consumer_commits_latest_at_exit(
    aio_consumer, config_post, messages_cb, record, record2
):
    aio_consumer.getmany.side_effect = [
        {TopicPartition(record.topic, record.partition): [record]},
        {TopicPartition(record2.topic, record2.partition): [record2]},
        ConsumerStoppedError,
    ]
    c = EVKafkaConsumer(config=config_post, messages_cb=messages_cb)

    t = c.startup()
    await asyncio.wait([t])

    aio_consumer.commit.assert_awaited_once_with(
        {TopicPartition(record2.topic, record2.partition): record2.offset + 1}
    )


async def test_consumer_immediate_commits(
    aio_consumer, config_post, messages_cb, record, record2
):
    config_post["auto_commit_interval_ms"] = 0
    aio_consumer.getmany.side_effect = [
        {TopicPartition(record.topic, record.partition): [record]},
        {TopicPartition(record2.topic, record2.partition): [record2]},
        ConsumerStoppedError,
    ]
    c = EVKafkaConsumer(config=config_post, messages_cb=messages_cb)

    t = c.startup()
    await asyncio.wait([t])

    aio_consumer.commit.assert_has_awaits(
        [
            call({TopicPartition(record.topic, record.partition): record.offset + 1}),
            call(
                {TopicPartition(record2.topic, record2.partition): record2.offset + 1}
            ),
        ]
    )


async def test_run_bg_commit_before_time(mocker, config_post, messages_cb, commit):
    monotonic = mocker.patch("evkafka.consumer.time.monotonic", return_value=1234)
    config_post["auto_commit_interval_ms"] = 2000
    c = EVKafkaConsumer(
        config=config_post,
        messages_cb=messages_cb,
        loop_interval_ms=10000,
        batch_max_size=1,
    )
    monotonic.return_value = 1234.1

    assert (await c.run_bg_commit()) == 1900

    commit.assert_not_awaited()


async def test_run_bg_commit_before_time_long_autocommit_period(
    mocker, config_post, messages_cb, commit
):
    monotonic = mocker.patch("evkafka.consumer.time.monotonic", return_value=1234)
    config_post["auto_commit_interval_ms"] = 2000
    c = EVKafkaConsumer(
        config=config_post,
        messages_cb=messages_cb,
        loop_interval_ms=500,
        batch_max_size=1,
    )
    monotonic.return_value = 1234.1

    assert (await c.run_bg_commit()) == 500

    commit.assert_not_awaited()


async def test_run_bg_commit_after_time(mocker, config_post, messages_cb, commit):
    monotonic = mocker.patch("evkafka.consumer.time.monotonic", return_value=1234)
    config_post["auto_commit_interval_ms"] = 2000
    c = EVKafkaConsumer(
        config=config_post,
        messages_cb=messages_cb,
        loop_interval_ms=10000,
        batch_max_size=1,
    )
    monotonic.return_value = 1237

    assert (await c.run_bg_commit()) == 2000

    commit.assert_awaited_once()


async def test_on_rebalance(config_post, messages_cb, commit):
    c = EVKafkaConsumer(config=config_post, messages_cb=messages_cb)

    await c.on_rebalance()

    commit.assert_awaited_once()


async def test_rebalance_listener(mocker):
    cb = mocker.AsyncMock()
    listener = RebalanceListener(cb)

    await listener.on_partitions_revoked([])

    cb.assert_awaited_once()


@pytest.mark.usefixtures("_getmany_returns_record_and_stops")
async def test_rebalance_waits_for_message_processing(config_post, commit):
    cb_in_progress = asyncio.Event()
    continue_cb = asyncio.Event()

    async def cb(*args):  # noqa: ARG001
        cb_in_progress.set()
        await continue_cb.wait()

    c = EVKafkaConsumer(config=config_post, messages_cb=cb, loop_interval_ms=1)
    c.startup()

    # ensure cb has taken a lock
    await cb_in_progress.wait()

    # launch "rebalance"
    rt = asyncio.create_task(c.on_rebalance())
    for _ in range(10):
        await asyncio.sleep(0)
    assert not rt.done(), "Rebalance is executed during message processing"
    commit.assert_not_awaited()

    # give handler a way and release the lock
    continue_cb.set()
    for _ in range(10):
        await asyncio.sleep(0)
    commit.assert_awaited()  # there would be actually 2 calls, the 2nd one at exit

    await c.shutdown()


async def test_consumer_does_not_commit_on_exception(
    aio_consumer, config_post, messages_cb
):
    aio_consumer.getmany.side_effect = [Exception]
    c = EVKafkaConsumer(config=config_post, messages_cb=messages_cb)

    t = c.startup()
    await asyncio.wait([t])

    aio_consumer.commit.assert_not_awaited()
