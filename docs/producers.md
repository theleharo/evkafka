# Producers


EVKafka uses a header `Event-Type` to match events against endpoints. 
You can either add this header explicitly while producing events or use an `EVKafkaProducer`:

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
## Producer configuration

Producer configuration is a dictionary containing poroducer settings.
```python
config = {
    "bootstrap_servers": "kafka:9092",
}
```
The producer is a tiny wrapper around `AIOKafkaProducer`. Full list of config options can be found 
in the official docs at the [AIOKafkaProducer](https://aiokafka.readthedocs.io/en/stable/api.html#producer-class) page.