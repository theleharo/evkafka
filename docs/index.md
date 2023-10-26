# Welcome to EVKafka

Handle kafka events easy.

**EVKafka** is a small framework for building event driven microservices 
with Apache Kafka and Python. It is based on asynchronous kafka client library 
[aiokafka](https://aiokafka.readthedocs.io/en/stable/).

Focus on event handling and the framework takes the rest.

## Features

- Easy to start and use
- Sync/async handlers are supported
- Extensible through consumer middleware
- Lifespan
- At-Least-Once/At-Most-Once delivery

## Installation

     $ pip install evkafka

## Introduction

### Example consumer app

A simplest possible consumer app may look like this:

```python
from evkafka import EVKafkaApp

from models import FooEventModel


config = {
    "topics": ["topic"],
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}

app = EVKafkaApp(config=config)


@app.event('FooEvent')
async def foo_handler(event: FooEventModel) -> None:
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
async def bar_handler(event: BarEventModel) -> None:
    print(event)
```

### Example producer

```python
import asyncio

from evkafka import EVKafkaProducer
from pydantic import BaseModel

from models import FooEventModel


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

if __name__ == "__main__":
    asyncio.run(produce(FooEventModel(data="value"), "FooEvent"))
```