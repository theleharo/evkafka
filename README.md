# evkafka
[![Test](https://github.com/theleharo/evkafka/actions/workflows/test.yml/badge.svg)](https://github.com/theleharo/evkafka/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/theleharo/evkafka.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/theleharo/evkafka)
[![PyPI - Version](https://img.shields.io/pypi/v/evkafka)](https://pypi.org/project/evkafka/)

**EVKafka** is a small framework for building event driven 
microservices with Apache Kafka and Python.
It is based on asynchronous kafka client library 
[aiokafka](https://aiokafka.readthedocs.io/en/stable/).

## Features

- Easy to start and use
- Sync/async handlers are supported
- Extensible through consumer middleware
- Lifespan
- At-Least-Once/At-Most-Once delivery
- AsyncAPI documentation

## Installation

     $ pip install evkafka

## Basic consumer
```python
from pydantic import BaseModel

from evkafka import EVKafkaApp
from evkafka.config import ConsumerConfig


class FooEventPayload(BaseModel):
    user_name: str


config: ConsumerConfig = {
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
    "topics": ["topic"],
}

app = EVKafkaApp(
    config=config,
    expose_asyncapi=True,
)


@app.event("FooEvent")
async def foo_handler(event: FooEventPayload) -> None:
    print(event)


if __name__ == "__main__":
    app.run()
```

## AsyncAPI documentation

![Screenshot](docs/img/asyncapi.png)


## Basic producer
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
    asyncio.run(produce({"user_name": "EVKafka"}, "FooEvent"))
```

More details can be found in the [documentation](https://evkafka.readthedocs.io/)


## Status

The framework is in alpha.

## License

This project is licensed under the terms of the  MIT license.
