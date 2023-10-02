import asyncio
import logging
import signal
import sys
import threading
import typing
import uuid
from types import FrameType

from .config import ConsumerConfig
from .consumer import Consumer
from .context import ConsumerCtx, Context, MessageCtx
from .handler import Handler
from .types import Wrapped

logger = logging.getLogger(__name__)


class EVKafkaApp:
    def __init__(
        self,
        config: ConsumerConfig | None = None,
        name: str | None = None,
    ) -> None:
        self._tasks: set[asyncio.Task[typing.Any]] = set()
        self._consumers: set[Consumer] = set()
        self.state: dict[str, typing.Any] = {}
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

    def run(self) -> None:
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
            return

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

        if self._default_consumer and self._default_handler:
            self.add_consumer(
                config=self._default_consumer["config"],
                handler=self._default_handler,
                name=self._default_consumer["name"],
            )

        if not self._consumer_configs:
            logger.error("No consumers defined")
            self.should_exit = True
            return

        # TODO ensure that every consumer has started otherwise need to stop gracefully
        for _name, config_items in self._consumer_configs.items():
            consumer = Consumer(
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

    def event(self, event_name: str | None = None) -> Wrapped:
        if self._default_consumer is None:
            raise RuntimeError(
                f"Event cannot be added because default consumer"
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
        app = handler

        async def messages_cb(
            message_ctx: MessageCtx,
            consumer_ctx: ConsumerCtx,
            app: Handler = app,
            state: dict[str, typing.Any] = self.state,
        ) -> None:
            context = Context(
                message=message_ctx,
                consumer=consumer_ctx,
                state=state.copy(),
            )
            return await app(context)

        name = name or str(uuid.uuid4())

        self._consumer_configs[name] = {
            "config": config,
            "messages_cb": messages_cb,
        }
