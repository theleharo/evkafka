# Events

EVKafka works with json encoded objects (dicts). In order to distinguish an event type 
a header `Message-Type` must be supplied alongside with a message at the producer side.

This can be done either manually or with a `EVKafkaProducer` wrapper around 
[AIOKafkaProducer](https://aiokafka.readthedocs.io/en/stable/api.html#producer-class):

```python
from evkafka import EVKafkaProducer


async def produce(event: bytes, event_name: str):
    config = {"bootstrap_servers": "kafka:9092"}

    async with EVKafkaProducer(config) as producer:
        await producer.send_event(
            topic='topic',
            event=event,
            event_name=event_name,
        )
```