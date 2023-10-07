# Lifespan

Lifespan handler inside `EVKafka` allows for an application 
to execute code before and after the main application cycle. 

```python
@asynccontextmanager
async def lifespan():
    async init_resources()
    yield
    async teardown_resources()

app = EVKafkaApp(lifespan=lifespan)
```

## State

You may want to share some objects between the lifespan and certain
endpoints. This might be a database connection or a producer instance
which are used to communicate with other services.

The lifespan can yield these objects in a dictionary which is later
accessible with a `State` object attached to a `Request` instance.


```python
import aiohttp
from contextlib import asynccontextmanager
from evkafka import EVKafkaApp, Request


@asynccontextmanager
async def lifespan():
    async with aiohttp.ClientSession() as session:
        yield {'client_session': session}

config = {
    ...
}

app = EVKafkaApp(config=config, lifespan=lifespan)


@app.event('Event')
async def handle_event(event: dict, request: Request):
    session = request.state.client_session
    async with session.post('http://example.com', data=event) as resp:
        assert resp.status == 200


app.run()
```
