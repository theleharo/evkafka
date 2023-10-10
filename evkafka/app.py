import asyncio
import logging
import signal
import sys
import threading
import typing
import uuid
from types import FrameType

from .config import ConsumerConfig
from .consumer import EVKafkaConsumer
from .context import AppContext, ConsumerCtx, Context, MessageCtx
from .handler import Handler
from .lifespan import LifespanManager
from .types import Lifespan, Wrapped

logger = logging.getLogger(__name__)


class EVKafkaApp:
    def __init__(
        self,
        config: ConsumerConfig | None = None,
        name: str | None = None,
        lifespan: Lifespan | None = None,
    ) -> None:
        self.force_exit = False
        self.should_exit = False
        self.started = False

        self._handler_cls = Handler
        self._default_handler: Handler | None = None
        self._consumer_configs: dict[str, dict[str, typing.Any]] = {}
        self._default_consumer: dict[str, typing.Any] | None = None
        if config:
            self._default_consumer = {
                "config": config,
                "name": name,
            }

        self._tasks: set[asyncio.Task[typing.Any]] = set()
        self._consumers: set[EVKafkaConsumer] = set()
        self._app_context = AppContext()
        self._lifespan_manager = LifespanManager(lifespan)

    def run(self) -> None:  # pragma:  no cover
        asyncio.run(self.serve())
        if not self.started:
            sys.exit(3)

    async def serve(self) -> None:
        self.install_signal_handlers()
        await self.startup()
        if self.should_exit:
            return
        await self.main()
        await self.shutdown()

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            return  # pragma: no cover

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.handle_exit, sig, None)

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        if self.should_exit and sig == signal.SIGINT:
            self.force_exit = True
        else:
            self.should_exit = True

    async def startup(self) -> None:
        logger.info("Starting consumer app")

        await self._lifespan_manager.start()
        if self._lifespan_manager.should_exit:
            self.should_exit = True
            return
        self._app_context.state = self._lifespan_manager.state

        if self._default_consumer and self._default_handler:
            self.add_consumer(
                config=self._default_consumer["config"],
                handler=self._default_handler,
                name=self._default_consumer["name"],
            )

        for _name, config_items in self._consumer_configs.items():
            consumer = EVKafkaConsumer(
                config=config_items["config"],
                messages_cb=config_items["messages_cb"],
            )
            self._consumers.add(consumer)
            self._tasks.add(consumer.startup())
        self.started = True

    async def main(self) -> None:
        while not self.should_exit:
            for task in self._tasks:
                if task.done():
                    self.should_exit = True
                    break
            await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        logger.info("Shutting down")

        if self.force_exit:
            # E.g. 2nd Ctrl-C from console
            return

        await asyncio.gather(*(consumer.shutdown() for consumer in self._consumers))
        await self._lifespan_manager.stop()

    def event(self, event_name: str) -> Wrapped:
        assert self._default_consumer, (
            f"Event cannot be added because default consumer "
            f'was not passed to "{self.__class__.__name__}()"'
        )

        if self._default_handler is None:
            self._default_handler = self._handler_cls()

        return self._default_handler.event(event_name)

    def add_consumer(
        self,
        config: ConsumerConfig,
        handler: Handler,
        name: str | None = None,
    ) -> None:
        async def type_middleware(
            context: Context,
            app: Handler = handler,
        ) -> None:
            for k, v in context.message.headers:
                if k == "Event-Type":
                    context.message.event_type = v.decode()
                    break
            return await app(context)

        async def messages_cb(
            message_ctx: MessageCtx,
            consumer_ctx: ConsumerCtx,
            app: typing.Any = type_middleware,
            app_context: AppContext = self._app_context,
        ) -> None:
            context = Context(
                message=message_ctx,
                consumer=consumer_ctx,
                state=app_context.state.copy(),
            )
            return await app(context)

        name = name or str(uuid.uuid4())

        self._consumer_configs[name] = {
            "config": config,
            "messages_cb": messages_cb,
        }
