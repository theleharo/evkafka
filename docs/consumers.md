# Consumers

Consumer configuration is a dictionary containing consumer settings.
```python
from evkafka.config import ConsumerConfig

config: ConsumerConfig = {
    "topics": ["topic"],
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}
```

The framework is built around [aiokafka](https://aiokafka.readthedocs.io/en/stable/). Many configuration options are derived straight
from the lib's settings which can be found at [AIOKafkaConsumer documentation](https://aiokafka.readthedocs.io/en/stable/api.html#consumer-class). 

> **Note:** EVKafka consumer always works in autocommit mode so `enable_auto_commit` parameter is not used.

### Delivery semantic
EVKafka allow to choose when to commit offsets. You can select either 
"at most once delivery" or "at least once delivery". The strategy 
is configured by `auto_commit_mode` parameter.

#### At least once delivery: post-commit
This is the default strategy when `auto_commit_mode` is omitted in config or when it explicitly set to `post-commit`.
Offsets are committed only after a message is processed by a handler or skipped if no suitable handler found. 
If event processing fails the message will be read and processed again. 

> **Note:** Make sure that your processing is idempotent.

#### At most once delivery: pre-commit
The strategy may be set by assigning `auto_commit_mode="pre-commit"`.
Offset is scheduled for commit as soon as a message is received by a consumer. `AIOKafkaConsumer` auto commit 
implementation is used. If subsequent event processing fails, the message may be lost.


## Parallel consumers
Sometimes you want to consume messages from different kafka instances, e.g. you're making 
an integration with other team living in another kafka cluster. However, for some reason
it is undesirable to have sub-services for this particular app.

EVKafka allows to manage parallel consumers with their respective handlers. Consider following example:

```python
app = EVkafkaApp()

app.add_consumer(internal_kafka_config, internal_handler)
app.add_consumer(external_kafka_config, external_handler)

app.run()
```

Other possible scenarios may include a migration case when you need to consume events with the same type
from old and new kafka cluster. In this case the same handler instance shall be passed to every consumer.
The framework creates an independent instance of a consumer for each `.add_consumer()` call. 
