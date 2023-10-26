# evkafka

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

## Installation

     $ pip install evkafka

## Basic consumer
```python
from evkafka import EVKafkaApp


config = {
    "topics": ["topic"],
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}

app = EVKafkaApp(config=config)


@app.event("FooEvent")
async def foo_handler(event: dict) -> None:
    print(event)


if __name__ == "__main__":
    app.run()
```

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
    asyncio.run(produce({"data": "value"}, "FooEvent"))
```

More details can be found in the [documentation](https://evkafka.readthedocs.io/)


## Status

The framework is in alpha.

## License

This project is licensed under the terms of the  MIT license.
