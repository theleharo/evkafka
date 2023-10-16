# Middleware

**EVKafka** supports application-wide middlewares which are getting
called for every consumed event. The framework includes a default middleware
stack that helps to decode json events and reveal its type. You can override
it to fit your needs.

## Default middleware stack

When an app instance is created without middleware the actual stack consists
of two standard middleware classes, `EventTypeHeaderMiddleware` and `JsonDecoderMiddleware`.
Here's how you add it in an explicit form:

```python
from evkafka import EVKafkaApp
from evkafka.middleware import Middleware, EventTypeHeaderMiddleware, JsonDecoderMiddleware


config = ...
middleware = [
    Middleware(EventTypeHeaderMiddleware),
    Middleware(JsonDecoderMiddleware),
]

app = EVKafkaApp(config=config, middleware=middleware)
```

  - `EventTypeHeaderMiddleware` extracts a message type from the `Event-Type` header;
  - `JsonDecoderMiddleware` decodes a bytes-encoded message into a python dictionary.

## Configuring middleware

Some middleware class may expect configuration options. For example, `EventTypeHeaderMiddleware`
got optional `type_header_name` argument to override default type header name:

```python
middleware = [
    Middleware(EventTypeHeaderMiddleware, type_header_name='Custom-Type-Header'),
    Middleware(JsonDecoderMiddleware),
]

app = EVKafkaApp(..., middleware=middleware)
```




