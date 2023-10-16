import logging
import typing

from evkafka.context import Context, HandlerType
from evkafka.utils import load_json

logger = logging.getLogger(__name__)


class Middleware:
    def __init__(self, cls: type, **options: typing.Any) -> None:
        self.cls = cls
        self.options = options


class EventTypeHeaderMiddleware:
    def __init__(self, app: HandlerType, type_header_name: str = "Event-Type") -> None:
        self.app = app
        self.type_header_name = type_header_name

    async def __call__(self, context: Context) -> None:
        for k, v in context.message.headers:
            if k == self.type_header_name:
                context.message.event_type = v.decode()
                break
        await self.app(context)


class JsonDecoderMiddleware:
    def __init__(self, app: HandlerType) -> None:
        self.app = app

    async def __call__(self, context: Context) -> None:
        context.message.decoded_value = load_json(context.message.value)
        await self.app(context)


default_stack = [
    Middleware(EventTypeHeaderMiddleware),
    Middleware(JsonDecoderMiddleware),
]
