# Endpoints
In order to handle an event you need to define a handler function or an *endpoint* and register it in the app:

```python
@app.event('Event')
async def handle_event(event: dict) -> None:
    await do_something_with(event)
```

A type of the event is passed to `event` decorator. When the app receives an event
it checks its type and matches against known endpoints. As soon as the endpoint is found it gets
called. A payload type is defined by endpoint argument's typing and may be passed either 
as a dict or as a pydantic object. 

```python
class Event(BaseModel):
    data: str
    
@app.event('Event'):
async def handle_event(event: Event) -> None:
    assert isinstance(event, Event)
```


A handler function is either `async def` or bare `def`:

```python
@app.event('Event')
def handle_event(event: dict) -> None:
    do_something_with(event)
```
In latter case handler function is executed in a thread pool.

