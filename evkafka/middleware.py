import logging
import typing

from evkafka.context import Context, HandlerApp
from evkafka.utils import load_json

logger = logging.getLogger(__name__)


class Middleware:
    def __init__(self, cls: type, **options: typing.Any) -> None:
        self.cls = cls
        self.options = options


class JsonTypedDecoderMiddleware:
    def __init__(self, app: HandlerApp, type_header_name: str = "Event-Type") -> None:
        self.app = app
        self.type_header_name = type_header_name

    async def __call__(self, context: Context) -> None:
        for k, v in context.message.headers:
            if k == self.type_header_name:
                context.message.event_type = v.decode()
                break

        async def decode_cb(context: Context = context) -> dict[typing.Any, typing.Any]:
            return load_json(context.message.value)

        context.message.decoded_value_cb = decode_cb
        await self.app(context)


default_stack = [
    Middleware(JsonTypedDecoderMiddleware),
]
