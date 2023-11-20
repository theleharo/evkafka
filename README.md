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
- Automatic API documentation

## Installation

     $ pip install evkafka

## Example

### Create a consumer

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

### Explore API documentation

Automatic documentation (based on [AsyncAPI](https://www.asyncapi.com/)) is build and served at
http://localhost:8080.

![Screenshot](docs/img/asyncapi.png)

### Add a producer

```python
from contextlib import asynccontextmanager

from pydantic import BaseModel

from evkafka import EVKafkaApp, EVKafkaProducer, Handler, Request
from evkafka.config import ConsumerConfig, BrokerConfig, ProducerConfig


class FooEventPayload(BaseModel):
    user_name: str


class BarEventPayload(BaseModel):
    user_name: str
    message: str


handler = Handler()


@handler.event("FooEvent")
async def foo_handler(event: FooEventPayload, request: Request) -> None:
    print('Received FooEvent', event)
    new_event = BarEventPayload(user_name=event.user_name, message='hello')
    await request.state.producer.send_event(new_event, 'BarEvent')


@handler.event("BarEvent")
async def bar_handler(event: BarEventPayload) -> None:
    print('Received BarEvent', event)


@asynccontextmanager
async def lifespan():
    async with EVKafkaProducer(producer_config) as producer:
        yield {'producer': producer}


if __name__ == "__main__":
    broker_config: BrokerConfig = {
        "bootstrap_servers": "kafka:9092"
    }

    consumer_config: ConsumerConfig = {
        "group_id": "test",
        "topics": ["topic"],
        **broker_config
    }

    producer_config: ProducerConfig = {
        "topic": "topic",
        **broker_config
    }

    app = EVKafkaApp(
        expose_asyncapi=True,
        lifespan=lifespan
    )
    app.add_consumer(consumer_config, handler)
    app.run()

```

More details can be found in the [documentation](https://evkafka.readthedocs.io/)

## Status

The framework is in alpha.

## License

This project is licensed under the terms of the MIT license.
