# evkafka

**EVKafka** is a small framework for building event driven microservices.

A simplest possible app may look like this:

```python
from evkafka.app import EVKafkaApp

consumer_config = {
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}

app = EVKafkaApp(config=consumer_config, topics="topic")


@app.event('FooEvent')
def foo_handler(event: dict) -> None:
    print(event)


if __name__ == "__main__":
    app.run()
```

## Usage

The framework is in pre-alpha. There are a lot of things to do include docs.
