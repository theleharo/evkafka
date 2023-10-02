# Welcome to EVKafka

Handle kafka events easy.

**EVKafka** is a small framework for building event driven microservices.
It is based upon [aiokafka](https://aiokafka.readthedocs.io/en/stable/) and inspired
by wonderful [FastAPI](https://fastapi.tiangolo.com/).

Focus on event handling and the framework takes the rest.


## Example

A simplest possible app may look like this:

```python
from evkafka import EVKafkaApp


config = {
    "topics": ["topic"],
    "bootstrap_servers": "kafka:9092",
    "group_id": "test",
}

app = EVKafkaApp(config=config)


@app.event('FooEvent')
def foo_handler(event: dict) -> None:
    print(event)


if __name__ == "__main__":
    app.run()
```