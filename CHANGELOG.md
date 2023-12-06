### 0.6.1 (2023-12-06)

**Fixed**
- Remove incorrect import from non required dependency 'kafka-python'

### 0.6.0 (2023-12-03)

**Added**
 - Declarative definition of produced events via `Sender.event`

### 0.5.0 (2023-11-20)

**Added**
 - Basic AsyncApi schema generation
 - NOTICE.md

**Updated**
 - Documentation for `ConsumerConfig`, `ProducerConfig`
 - **breaking**: remove `max_poll_interval_ms`, `rebalance_timeout_ms` from consumer
config, replace with `max_endpoint_exec_time_ms`

### 0.4.0 (2023-10-27)

**Added**
 - `pre-commit` and `post-commit` consumer mode 

**Updated**
 - TestClient accepts non encoded event

**Removed**
 - `enable_auto_commit` from consumer config

### 0.3.0 (2023-10-17)

**Added**:
 - Message decode logic is moved to a middleware

**Updated**
 - Context obj new field 'decoded_value_cb'
 - **breaking**: request.json is now awaitable

### 0.2.0 (2023-10-14)

**Added**:
 - TestClient

### 0.1.0 (2023-10-10)

initial version