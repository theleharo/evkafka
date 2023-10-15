# Producers


**EVKafka** uses a header `Event-Type` to match events against endpoints. 
You can either add this header explicitly while producing events or use an `EVKafkaProducer`:

```python
from evkafka import EVKafkaProducer


async def produce(event: dict, event_type: str):
    config = {
        "topic": "topic", 
        "bootstrap_servers": "kafka:9092"
    }

    async with EVKafkaProducer(config) as producer:
        await producer.send_event(
            event=event,
            event_type=event_type,
        )
```
If events are being sent to a different topics you may skip adding a default topic to config
and pass it to `send_event` call directly.
```python
    await producer.send_event(
        event=event,
        event_type=event_type,
        topic=topic,
    )
```

## Event object

An event object is expected to have one of the following types:

- `dict`
- `str`
- `bytes`
- pydantic models

## Producer configuration

Producer configuration is a dictionary containing producer settings.
```python
config = {
    "bootstrap_servers": "kafka:9092",
    
}
```
`EVKafkaProducer` is a tiny wrapper around `AIOKafkaProducer`. Full list of config options can be found 
in the official docs at the [AIOKafkaProducer](https://aiokafka.readthedocs.io/en/stable/api.html#producer-class) page.
