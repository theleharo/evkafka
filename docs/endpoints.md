# Endpoints

In order to receive or send an event you need to define 
*endpoint* functions and register them within the app.

## Inbound endpoint

Inbound endpoints are functions that are executed when a consumer receives
events. A `Handler` object is used to route events to their endpoints. 
To indicate which function should handle a particular event, wrap it with 
the `handler.event()` decorator:

```python
from evkafka import Handler

handler = Handler()

@handler.event('Event')
async def handle_event(event: EventPayload) -> None:
    await do_something_with(event)
```

You can define an endpoint for every event type that you need to handle.

### Event matching

The name of the event is passed to the `event` decorator. When the app 
receives an event, it checks its type and matches against known endpoints. 
To distinguish the event type a header `Event-Type` must be supplied 
along with the message on the producer side. Once the endpoint is found,
it called with the event value. Unmatched events are silently skipped.

> **Note:** Event type header name may be overriden, 
see [Middleware](middleware.md).

### Payload types

A payload type is defined by the typing of the endpoint's argument 
in EVKafka. EVKafka supports the following types:

- `dict`
- `str`
- `bytes`
- pydantic models

For example if you want to have a dict inside an endpoint, you can
define it like this:

```python
@app.event('Event')
async def handle_event(event: dict) -> None:
    assert isinstance(event, dict)
```

> **Note:** if an endpoint expects a dict or pydantic object, 
the Kafka message value must be a valid JSON. However, there 
is no such limitation if events are processed as raw bytes.

### Endpoint extra

You may also supply an additional argument to capture a `Request`
object in order to obtain metadata about the current event:

```python
from evkafka import Request

from models import EventPayload


@app.event('Event')
async def handle_event(event: EventPayload, request: Request) -> None:
    assert 'Some-Header' in request.headers
```

By including the `request` argument in your endpoint function, 
you can access metadata such as the event's headers, key, topic, and other 
relevant information.

### Handler function type

In EVKafka, a handler function can be either an async def or a bare def:

```python
@app.event('Event')
def handle_event(event: bytes) -> None:
    do_something_with(event)
```
In the case of a bare def (non-async), the handler function 
is executed in a thread pool.

### Combining handlers

The `Handler` object has a method called `include_handler()` which
can be used to combine multiple handler instances into a single handler:

```python
from evkafka import Handler
from product_endpoints import handler as product_handler
from cart_endpoints import handler as cart_handler

handler = Handler()
handler.include_handler(product_handler)
handler.include_handler(cart_handler)

```
The new `handler` instance now includes all endpoints from 
the descending handlers (`product_handler` and `cart_handler`).

### Consuming events

To consume events from Kafka in EVKafka, each handler 
needs to be added to the app along with a consumer 
configuration using the `.add_consumer()` method. Assuming 
you have a handler defined in `handlers.py`, you can 
add a consumer with this handler to the app as follows:

```python
from evkafka import EVKafkaApp
from handlers import handler

if __name__ == '__main__':
    config = {...}  # Specify your consumer configuration
    app = EVKafkaApp()
    app.add_consumer(config, handler)
    
    app.run()
```
Once the consumer is added, you can call `app.run()` to start 
the event consumption process.

For more detailed information about consumer configuration, 
please refer to the [Consumers](consumers.md) documentation. 

## Outbound endpoint

An outbound endpoint in EVKafkaApp provides a convenient 
way to produce events without writing additional code. 
Unlike [inbound endpoints](#inbound-endpoint), which handle 
incoming events, outbound endpoints are designed 
to be called by users to send events.

To define an outbound endpoint, you can utilize the `Sender` 
object from **EVKafka**. By wrapping a function with 
the `sender.event()` decorator, it becomes an outbound 
endpoint capable of producing events.

```python
from evkafka import Sender


sender = Sender()


@sender.event('Event')
async def send_event(e: EventPayload) -> None:
    pass
```
In the example above, the `send_event` function is defined 
as an outbound endpoint for the event type 'Event'. 
It can be called by users to send events using the provided payload.

### Payload types

The event object expected by EVKafka can have one
of the following types:

- `dict`
- `str`
- `bytes`
- pydantic models

EVKafka handles the serialization and publication of 
the event objects to the Kafka broker. A header `Event-Type`
is automatically added to every outgoing message.

### Producing events
To produce events in EVKafka, you need to add each sender 
to the app along with a producer configuration using 
the `.add_producer()` method. Assuming you have a sender
defined in `senders.py`, you can add a producer with this sender
to the app as shown below:


```python
from evkafka import EVKafkaApp
from senders import sender

if __name__ == '__main__':
    config = {...}  # Specify your producer configuration
    app = EVKafkaApp()
    app.add_producer(config, sender)
    
    app.run()
```
Once the producer is added and the app is started by 
an `app.run()` call, outbound endpoints are ready to send events.

For more information about producer configuration, 
please refer to the [Producers](producers.md) documentation. 


### Outbound topic configuration

A default topic to produce events can be supplied with the `config` dict
in the `app.add_producer` call. You can also specify the topic for a particular
outbound endpoint:

```python
@sender.event('Event', topic='other-topic')
async def send_event(e: EventPayload) -> None:
    pass
```

The topic must be defined either in the common producer configuration or
for the outbound event.
