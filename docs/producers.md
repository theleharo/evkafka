# Producers


**EVKafka** uses a header `Event-Type` to match events against endpoints. 
You can either add this header explicitly while producing events or use an `EVKafkaProducer`:

```python
from evkafka import EVKafkaProducer
from pydantic import BaseModel


async def produce(event: BaseModel, event_type: str):
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

## Producer instance lifetime

Usually you don't want to instantiate a producer every time you need to produce an event. A common way
is to run async context manager once at application lifespan. This might be the **EVKafka** [lifespan](lifespan.md)
or FastAPI/[Starlette](https://www.starlette.io/lifespan/).
