"""
The description below is mostly taken from `aiokafka`. Some parameters of
the original client are not used/not applicable in this realization and are set to reasonable
default values.
"""
from typing import Any, Callable

from pydantic import RootModel
from typing_extensions import Required, TypedDict


class BrokerConfig(TypedDict, total=False):
    bootstrap_servers: str | list[str]
    """
    A string 'host[:port]' (or list of 'host[:port]' strings) that the consumer should contact to
    bootstrap initial cluster metadata. This does not have to be the full node list. It just needs
    to have at least one broker that will respond to Metadata API Request. Default port is 9092.
    If no servers are specified, will default to localhost:9092.
    """

    client_id: str
    """
    A name for this client. This string is passed in each request to servers and can be used to
    identify specific server-side log entries that correspond to this client. Also submitted to
    GroupCoordinator for logging with respect to consumer group administration.
    Default: 'aiokafka-{ver}'.
    """

    metadata_max_age_ms: int
    """
    The period of time in milliseconds after which we force a refresh of metadata even if we haven't
    seen any partition leadership changes to proactively discover any new brokers or partitions.
    Default: 300000.
    """

    request_timeout_ms: int
    """ Client request timeout in milliseconds. Default: 40000. """

    retry_backoff_ms: int
    """ Milliseconds to backoff when retrying on errors. Default: 100. """

    ssl_context: Any
    """
    (ssl.SSLContext) Pre-configured SSLContext for wrapping socket connections. For more information
    see :ref:`ssl_auth`. Default: None.
    """

    security_protocol: str
    """
    Protocol used to communicate with brokers. Valid values are: PLAINTEXT, SSL, SASL_PLAINTEXT,
    SASL_SSL. Default: PLAINTEXT.
    """

    api_version: str
    """
    Specify which kafka API version to use. AIOKafka supports Kafka API versions >=0.9 only. If set
    to 'auto', will attempt to infer the broker version by probing various APIs. Default: auto.
    """

    connections_max_idle_time: int
    """
    Close idle connections after the number of milliseconds specified by this config. Specifying
    `None` will disable idle checks. Default: 540000 (9 minutes).
    """

    sasl_mechanism: str
    """
    Authentication mechanism when security_protocol is configured for ``SASL_PLAINTEXT``
    or ``SASL_SSL``. Valid values are: ``PLAIN``, ``GSSAPI``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``,
    ``OAUTHBEARER``. Default: ``PLAIN``.
    """

    sasl_plain_username: str
    """ Username for SASL ``PLAIN`` authentication. Default: None. """

    sasl_plain_password: str
    """ Password for SASL ``PLAIN`` authentication. Default: None. """

    sasl_oauth_token_provider: Any
    """
    (aiokafka.abc.AbstractTokenProvider) OAuthBearer token provider instance.
    (See :mod:`kafka.oauth.abstract`). Default: None.
    """

    cluster_name: str | None
    """ Optional name for brokers. Used in AsyncAPI documentation. """

    cluster_description: str | None
    """ Optional description for brokers. Used in AsyncAPI documentation. """


BrokerConfigModel = RootModel[BrokerConfig]


class TopicConfig(TypedDict, total=False):
    name: Required[str]
    """ Kafka topic name """

    description: str | None
    """ Optional description for this topic. Used in AsyncAPI documentation. """


class ConsumerConfig(BrokerConfig, total=False):
    topics: list[str] | list[TopicConfig]
    """ List of topics to subscribe to. """

    group_id: str
    """
    Name of the consumer group to join for dynamic partition assignment, and to use for fetching and
    committing offsets.
    """

    fetch_min_bytes: int
    """
    Minimum amount of data the server should return for a fetch request, otherwise wait up
    to `fetch_max_wait_ms` for more data to accumulate. Default: 1.
    """

    fetch_max_bytes: int
    """
    The maximum amount of data the server should return for a fetch request. This is not an absolute
    maximum, if the first message in the first non-empty partition of the fetch is larger than this
    value, the message will still be returned to ensure that the consumer can make progress.
    NOTE: consumer performs fetches to multiple brokers in parallel so memory usage will depend on
    the number of brokers containing partitions for the topic. Supported Kafka version >= 0.10.1.0.
    Default: 52428800 (50 Mb).
    """

    fetch_max_wait_ms: int
    """
    The maximum amount of time in milliseconds the server will block before answering the fetch
    request if there isn't sufficient data to immediately satisfy the requirement given by
    fetch_min_bytes. Default: 500.
    """

    max_partition_fetch_bytes: int
    """
    The maximum amount of data per-partition the server will return. The maximum total memory used
    for a request ``= #partitions * max_partition_fetch_bytes``. This size must be at least as large
    as the maximum message size the server allows or else it is possible for the producer to send
    messages larger than the consumer can fetch. If that happens, the consumer can get stuck trying
    to fetch a large message on a certain partition. Default: 1048576.
    """

    auto_offset_reset: str
    """
    A policy for resetting offsets on :exc:`.OffsetOutOfRangeError` errors: ``earliest`` will move
    to the oldest available message, ``latest`` will move to the most recent, and ``none`` will
    raise an exception so you can handle this case. Default: ``latest``.
    """

    auto_commit_mode: str
    """
    A strategy for automatic committing offsets which determines a delivery semantic for this
    consumer. You can select either "at most once delivery" using pre-commit strategy or "at least
    once delivery" with post-commit strategy.
    Valid values are: ``pre-commit``, ``post-commit``. Default: ``post-commit``.
    """

    auto_commit_interval_ms: int
    """ Milliseconds between automatic offset commits. Default: 5000."""

    check_crcs: bool
    """
    Automatically check the CRC32 of the records consumed. This ensures no on-the-wire or on-disk
    corruption to the messages occurred. This check adds some overhead, so it may be disabled in
    cases seeking extreme performance. Default: True.
    """

    partition_assignment_strategy: list
    """
    List of objects to use to distribute partition ownership amongst consumer instances when group
    management is used. This preference is implicit in the order of the strategies in the list.
    When assignment strategy changes: to support a change to the assignment strategy, new versions
    must enable support both for the old assignment strategy and the new one. The coordinator will
    choose the old assignment strategy until all members have been updated. Then it will choose the
    new strategy. Default: [:class:`.RoundRobinPartitionAssignor`]
    """

    max_endpoint_exec_time_ms: int
    """
    Maximum allowed time for executing an endpoint's handler. If this timeout is exceeded the
    consumer is considered failed and the group will rebalance in order to reassign the partitions
    to another consumer group member. Internally in the EVKafka consumer wrapper this value is used
    to set both `max_poll_interval_ms` and `rebalance_timeout_ms`. Default 20000.
    """

    session_timeout_ms: int
    """
    Client group session and failure detection timeout. The consumer sends periodic heartbeats
    (`heartbeat.interval.ms`) to indicate its liveness to the broker. If no hearts are received
    by the broker for a group member within the session timeout, the broker will remove the consumer
    from the group and trigger a rebalance. The allowed range is configured with the **broker**
    configuration properties `group.min.session.timeout.ms` and `group.max.session.timeout.ms`.
    Default: 10000.
    """

    heartbeat_interval_ms: int
    """
    The expected time in milliseconds between heartbeats to the consumer coordinator when using
    Kafka's group management feature. Heartbeats are used to ensure that the consumer's session
    stays active and to facilitate rebalancing when new consumers join or leave the group. The value
    must be set lower than `session_timeout_ms`, but typically should be set no higher than 1/3 of
    that value. It can be adjusted even lower to control the expected time for normal rebalances.
    Default: 3000.
    """

    consumer_timeout_ms: int
    """
    Maximum wait timeout for background fetching routine. Mostly defines how fast the system will
    see rebalance and request new data for new partitions. Default: 200.
    """

    # Other aiokafka consumer configuration options:
    #   exclude_internal_topics: bool - always on
    #   enable_auto_commit: bool - is set automatically in a wrapper
    #   isolation_level: str - not used, transactions are not supported
    #   key_deserializer - not used
    #   value_deserializer - not used
    #   max_poll_records - not used
    #   max_poll_interval_ms: int - set to max_endpoint_exec_time_ms
    #   rebalance_timeout_ms: int - set to max_endpoint_exec_time_ms


class ProducerConfig(BrokerConfig, total=False):
    topic: str | None
    """
    A default topic where the message will be published if topic is not provided with
    `EVKafkaProducer.send_event` call. """

    acks: Any
    """
    One of ``0``, ``1``, ``all``. The number of acknowledgments the producer requires the leader
    to have received before considering a request complete. This controls the durability of records
    that are sent. The following settings are common:

        * ``0``: Producer will not wait for any acknowledgment from the server
          at all. The message will immediately be added to the socket
          buffer and considered sent. No guarantee can be made that the
          server has received the record in this case, and the retries
          configuration will not take effect (as the client won't
          generally know of any failures). The offset given back for each
          record will always be set to -1.
        * ``1``: The broker leader will write the record to its local log but
          will respond without awaiting full acknowledgement from all
          followers. In this case should the leader fail immediately
          after acknowledging the record but before the followers have
          replicated it then the record will be lost.
        * ``all``: The broker leader will wait for the full set of in-sync
          replicas to acknowledge the record. This guarantees that the
          record will not be lost as long as at least one in-sync replica
          remains alive. This is the strongest available guarantee.

    If unset, defaults to ``acks=1``. If `enable_idempotence` is `True` defaults to ``acks=all``.
    """

    compression_type: str
    """
    The compression type for all data generated by the producer. Valid values are ``gzip``,
    ``snappy``, ``lz4``, ``zstd`` or `None`. Compression is of full batches of data, so the efficacy
    of batching will also impact the compression ratio (more batching means better compression).
    Default: `None`.
    """

    max_batch_size: int
    """
    Maximum size of buffered data per partition. After this amount `send` coroutine will block until
    batch is drained. Default: 16384.
    """

    linger_ms: int
    """
    The producer groups together any records that arrive in between request transmissions into
    a single batched request. Normally this occurs only under load when records arrive faster than
    they can be sent out. However in some circumstances the client may want to reduce the number of
    requests even under moderate load. This setting accomplishes this by adding a small amount of
    artificial delay; that is, if first request is processed faster, than `linger_ms`, producer will wait
    ``linger_ms - process_time``. Default: 0 (i.e. no delay).
    """

    partitioner: Callable
    """
    Callable used to determine which partition each message is assigned to. Called (after key
    serialization): ``partitioner(key_bytes, all_partitions, available_partitions)``. The default
    partitioner implementation hashes each non-None key using the same murmur2 algorithm as the Java
    client so that messages with the same key are assigned to the same partition. When a key is
    `None`, the message is delivered to a random partition (filtered to partitions with available
    leaders only, if possible).
    """

    max_request_size: int
    """
    The maximum size of a request. This is also effectively a cap on the maximum record size. Note
    that the server has its own cap on record size which may be different from this. This setting
    will limit the number of record batches the producer will send in a single request to avoid
    sending huge requests. Default: 1048576.
    """

    enable_idempotence: bool
    """
    When set to `True`, the producer will ensure that exactly one copy of each message is written
    in the stream. If `False`, producer retries due to broker failures, etc., may write duplicates
    of the retried message in the stream. Note that enabling idempotence acks to set to ``all``.
    If it is not explicitly set by the user it will be chosen. If incompatible values are set,
    a :exc:`ValueError` will be thrown.
    """

    # Other aiokafka producer configuration options:
    #   key_serializer: Callable - not used
    #   value_serializer: Callable - not used
