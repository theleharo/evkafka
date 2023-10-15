# Testing

You can test your **EVKafka** consumers code using `TestClient`. The client
exposes an interface similar to producer's and allows to "send" events
to handlers directly from `pytest` tests.

## Using `TestClient`

Consider having the application code in `main.py`:
```python
from evkafka import EVKafkaApp


app = EVKafkaApp(config={"topics": ["topic"]})


@app.event("Event")
async def handler(e: dict):
    await store_event(e)

async def store_event(e: dict):
    pass

```
We want to make sure that `store_event` receives an expected event. Then we could
write our test using `TestClient` as following (assume `pytest-mock` is installed):

```python
from evkafka import TestClient

from main import app


def test_store_event(mocker):
    mock_store_event = mocker.patch('main.store_event', new_callable=mocker.AsyncMock)

    with TestClient(app) as client:
        client.send_event(
            topic='topic',
            event=b'{"key":"value"}',
            event_type='Event'
        )

    mock_store_event.assert_awaited_once_with({'key': 'value'})

```
Note, `TestClient` works only with normal `def` fixtures and test functions, not `async def`.
You're still able to use `AsyncMock` and check whether mocked coroutines were awaited
as in the example above.

## Multiple Consumers

A `send_event` is able to send an event to any registered consumer. If there is only one
consumer it is selected automatically. However, when there are few of them `TestClient`
needs to know what handlers you want it to communicate with. In this case you need to register
consumers with names:
```python
# in main module
app.add_consumer(..., name='foo-consumer')

# in tests
def test_store_event():
    with TestClient(app) as client:
        client.send_event(
            topic='topic',
            event=b'{"key":"value"}',
            event_type='Event',
            consumer_name='foo-consumer',
        )

```

## Running Lifespan in tests

When used as a context manager `TestClient` calls an application lifespan automatically (if present).

```python
def test_store_event():
    with TestClient(app) as client:
        # call the application's lifespan startup
        client.send_event(...)
    
    # call the lifespan's teardown
```