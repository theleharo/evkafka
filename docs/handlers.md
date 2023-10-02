# Handlers

Internally every event source (a consumer instance) must be attached
to a corresponing `Handler` which routes events to their respective endpoints. 
The `EVKafkaApp` allows to register endpoints to default handler however it may be more
convenient to split handlers and an application entry point onto different files.

In endpoints.py:

```python
from evkafka import Handler

handler = Handler()


@handler.event('Event')
def handle_event(e: dict) -> None:
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

Note that `Consumer`<->`Handler` link is defined explicitly by `.add_consumer()` call.

It also worth mentioning that `Handler` has `include_handler()` method which
can be used to combine several handler instances into one:

```python
from evkafka import Handler
from product_endpoints import handler as product_handler
from cart_endpoints import handler as cart_handler

handler = Handler()
handler.include_handler(product_handler)
handler.include_handler(cart_handler)

```

