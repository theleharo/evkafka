# Consumers

## Consumer configuration
Consumer configuration is a simple dictionary containing consumer settings.
```python
config = {
    "topics": ["topic"],
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}
```
The framework is built around [aiokafka](https://aiokafka.readthedocs.io/en/stable/). For full list of options 
check the lib's [AIOKafkaConsumer documentation](https://aiokafka.readthedocs.io/en/stable/api.html#consumer-class).


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
from old and new kafka cluster. In this case the same handler instance shall be passed to every consumer:

```python
app = EVkafkaApp()

app.add_consumer(config, handler)
app.add_consumer(new_config, handler)

app.run()
```
The framework creates an independent instance of a consumer for each `.add_consumer()` call. 
