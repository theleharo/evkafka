# evkafka

**EVKafka** is a small framework for building event driven microservices.

## Installation

     $ pip install evkafka

## Basic usage
```python
from evkafka.app import EVKafkaApp

config = {
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}

app = EVKafkaApp(config=config, topics="topic")


@app.event('FooEvent')
def foo_handler(event: dict) -> None:
    print(event)


if __name__ == "__main__":
    app.run()
```

More details can be found in the [documentation](https://evkafka.readthedocs.io/)


## Status

The framework is in alpha.

## License

This project is licensed under the terms of the  MIT license.
