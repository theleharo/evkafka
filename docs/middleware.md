# Middleware

**EVKafka** supports application-wide middlewares which are getting
called for every consumed event. The framework includes a default middleware
stack that helps to decode json events and reveal its type. You can override
it to fit your needs.

## Default middleware stack

When an app instance is created without middleware the actual stack consists
of a standard middleware class `JsonTypedDecoderMiddleware`.
Here's how you add it in an explicit form:

```python
from evkafka import EVKafkaApp
from evkafka.middleware import Middleware, JsonTypedDecoderMiddleware


config = ...
middleware = [
    Middleware(JsonTypedDecoderMiddleware),
]

app = EVKafkaApp(config=config, middleware=middleware)
```

`JsonTypedDecoderMiddleware` extracts a message type from the `Event-Type` header and provide
a callback to decode a bytes-encoded message into a python dictionary. Event is not decoded if
there is no matching endpoint exists.

## Configuring middleware

Some middleware class may expect configuration options. For example, `JsonTypedDecoderMiddleware`
got optional `type_header_name` argument to override default type header name:

```python
middleware = [
    Middleware(JsonTypedDecoderMiddleware, type_header_name='Custom-Type-Header'),
]

app = EVKafkaApp(..., middleware=middleware)
```




