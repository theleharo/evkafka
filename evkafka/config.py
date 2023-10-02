from typing import TYPE_CHECKING, Callable, TypedDict

if TYPE_CHECKING:
    import ssl

    import aiokafka  # type: ignore


class ConsumerConfig(TypedDict, total=False):
    topics: list[str]
    bootstrap_servers: str | list[str]
    client_id: str
    group_id: str | None
    key_deselializer: Callable
    value_deselializer: Callable
    fetch_min_bytes: int
    fetch_max_bytes: int
    fetch_max_wait_ms: int
    max_partition_fetch_bytes: int
    max_poll_records: int
    request_timeout_ms: int
    retry_backoff_ms: int
    auto_offset_reset: str
    enable_auto_commit: bool
    auto_commit_interval_ms: int
    check_crcs: bool
    metadata_max_age_ms: int
    partition_assignment_strategy: list
    max_poll_interval_ms: int
    rebalance_timeout_ms: int
    session_timeout_ms: int
    heartbeat_interval_ms: int
    consumer_timeout_ms: int
    api_version: str
    security_protocol: str
    ssl_context: "ssl.SSLContext"
    exclude_internal_topics: bool
    connections_max_idle_time: int
    isolation_level: str
    sasl_mechanism: str
    sasl_plain_username: str
    sasl_plain_password: str
    sasl_oauth_token_provider: "aiokafka.abc.AbstractTokenProvider"
