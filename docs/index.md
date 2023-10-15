# Welcome to EVKafka

Handle kafka events easy.

**EVKafka** is a small framework for building event driven microservices 
with Apache Kafka and Python. It is based upon 
[aiokafka](https://aiokafka.readthedocs.io/en/stable/) and inspired
by wonderful [FastAPI](https://fastapi.tiangolo.com/).

Focus on event handling and the framework takes the rest.

## Installation

     $ pip install evkafka

## Introduction

### Example consumer app

A simplest possible consumer app may look like this:

```python
from evkafka import EVKafkaApp


config = {
    "topics": ["topic"],
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}

app = EVKafkaApp(config=config)


@app.event('FooEvent')
async def foo_handler(event: dict) -> None:
    print(event)


if __name__ == "__main__":
    app.run()
```

The application connects to kafka broker and starts to read kafka messages. As soon as a message
of type `FooEvent` is received the app calls the handler function `foo_handler` with 
the message object in `event` parameter.

It worth nothing to add another handler function to process another message type:

```python
@app.event('BarEvent')
async def bar_handler(event: dict) -> None:
    print(event)
```

### Example producer

```python
import asyncio
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

if __name__ == "__main__":
    asyncio.run(produce({"data": "value"}, "FooEvent"))
```