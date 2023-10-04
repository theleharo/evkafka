# Endpoints

In order to handle an event you need to define a handler function or an *endpoint* and register it in the app:

```python
@app.event('Event')
async def handle_event(event: dict) -> None:
    await do_something_with(event)
```

You can define an endpoint for an every event type you need to handle.

## Event matching

A name of the event is passed to an `event` decorator. When the app receives an event
it checks its type and matches against known endpoints. To distinguish an event type 
a header `Message-Type` must be supplied alongside with a message at the producer side.
As soon as the endpoint is found it gets called with the event value. 
Unmatched events are silently skipped.

## Endpoint payload types

A payload type is defined by an endpoint argument's typing. Evkafka supports 
following types:

- `dict`
- `str`
- `bytes`
- pydantic models

For example, to have a pydantic object inside an endpoint:

```python
from pydantic import BaseModel


class Event(BaseModel):
    data: str
    
@app.event('Event'):
async def handle_event(event: Event) -> None:
    assert isinstance(event, Event)
```

## Kafka message types

A kafka message must be valid json if an endpoint expects `dict` or pydantic object. However
there is no such limitation if events are processed as raw `bytes`.

## Handler function type

A handler function is either `async def` or bare `def`:

```python
@app.event('Event')
def handle_event(event: dict) -> None:
    do_something_with(event)
```
In latter case handler function is executed in a thread pool.

