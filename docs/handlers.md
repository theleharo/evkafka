# Handlers

Internally an every event source (a consumer instance) must be attached
to a corresponing `Handler` which routes events to their respective endpoints. 
In the case when a consumer configuration is supplied to the `EVKafkaApp` directly
you can use the app instance to register endpoints to default handler.

However, it may be more convenient to put handlers and an application 
entry point into different files.

In endpoints.py:

```python
from evkafka import Handler

from models import EventPayload


handler = Handler()


@handler.event('Event')
def handle_event(e: EventPayload) -> None:
    ...
```

In main.py:

```python
from evkafka import EVKafkaApp
from endpoints import handler

if __name__ == '__main__':
    config = {...}
    app = EVKafkaApp()
    app.add_consumer(config, handler)
    
    app.run()
```

Every handler should be added to the app alongside with a consumer configuration 
explicitly by an `.add_consumer()` call.
Please see the [Consumers](consumers.md) for further details. 

## Combining handlers

The `Handler` object has the `include_handler()` method which
can be used to combine several handler instances into one:

```python
from evkafka import Handler
from product_endpoints import handler as product_handler
from cart_endpoints import handler as cart_handler

handler = Handler()
handler.include_handler(product_handler)
handler.include_handler(cart_handler)

```

The new handler includes all endpoints from descending handlers.