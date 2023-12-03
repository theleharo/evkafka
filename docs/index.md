# Welcome to EVKafka

Handle kafka events made easy.

**EVKafka** is a lightweight framework for building 
event-driven microservices with Apache Kafka and Python.
It is based on the asynchronous Kafka client library 
[aiokafka](https://aiokafka.readthedocs.io/en/stable/).

Focus on event handling while the framework takes care of the rest.

## Features

- Easy to start and use
- Sync/async handlers are supported
- Extensible through consumer middleware
- Lifespan
- At-Least-Once/At-Most-Once event delivery guarantees
- Automatic API documentation generation


## Installation

     $ pip install evkafka

## Introduction

### Build a consumer app

A simplest possible consumer app may look like this:

```python
from evkafka import EVKafkaApp
from evkafka.config import ConsumerConfig
from pydantic import BaseModel


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

The application connects to the Kafka broker and begins 
reading kafka messages. Once a message of type `FooEvent` 
is received, the app calls the `foo_handler` handler function,
passing the message object as the `event` parameter.

> **Note**. Kafka broker should be available at `kafka:9092` to run the example. 

### Explore API documentation

Automatic documentation (based on [AsyncAPI](https://www.asyncapi.com/)) is build and served at
[http://localhost:8080](http://localhost:8080).
![Screenshot](img/asyncapi.png)

In our example, the topic is represented as a channel 
in the documentation. AsyncAPI describes the application 
from a client perspective, specifying that the application 
expects `FooEvent` to be published to the channel.

### Add another event
It worth nothing to add another handler function to process different message type:

```python
class BarEventPayload(BaseModel):
    user_name: str
    message: str


@app.event('BarEvent')
async def bar_handler(event: BarEventPayload) -> None:
    print(event)
```

### Check documentation update

Restart your app. You should see an updated docs:
![Screenshot](img/asyncapi_2.png)


### Produce events with EVKafka

A producer may be instantiated within the app and used to produce new events:

```python
from evkafka import EVKafkaApp, Handler, Request, Sender
from evkafka.config import ConsumerConfig, BrokerConfig, ProducerConfig
from pydantic import BaseModel


sender = Sender()
handler = Handler()


class FooEventPayload(BaseModel):
    user_name: str


class BarEventPayload(BaseModel):
    user_name: str
    message: str


@sender.event('BarEvent')
async def send_bar(event: BarEventPayload) -> None:
    pass


@handler.event("FooEvent")
async def foo_handler(event: FooEventPayload, request: Request) -> None:
    print('Received FooEvent', event)
    new_event = BarEventPayload(user_name=event.user_name, message='hello')
    await send_bar(new_event)


@handler.event("BarEvent")
async def bar_handler(event: BarEventPayload) -> None:
    print('Received BarEvent', event)


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

    app = EVKafkaApp(expose_asyncapi=True)
    app.add_consumer(consumer_config, handler)
    app.add_producer(producer_config, sender)
    app.run()
```

> **Feature Note.** Documentation for produced events will be included in next releases
