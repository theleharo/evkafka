import asyncio
import logging
import signal
import sys
import threading
import typing
import uuid
from types import FrameType

from .asyncapi.server import AsyncApiServer
from .asyncapi.spec import get_asyncapi_spec
from .config import ConsumerConfig, ProducerConfig
from .consumer import EVKafkaConsumer
from .context import AppContext, ConsumerCtx, Context, HandlerApp, MessageCtx
from .handler import Handler
from .lifespan import LifespanManager
from .middleware import Middleware, default_stack
from .producer import EVKafkaProducer
from .sender import Sender
from .types import Lifespan, Wrapped

logger = logging.getLogger(__name__)


class EVKafkaApp:
    def __init__(
        self,
        config: ConsumerConfig | None = None,
        name: str | None = "default",
        middleware: typing.Sequence[Middleware] | None = None,
        lifespan: Lifespan | None = None,
        title: str = "EVKafka",
        version: str = "0.1.0",
        description: str | None = None,
        terms_of_service: str | None = None,
        contact: dict[str, str] | None = None,
        license_info: dict[str, str] | None = None,
        expose_asyncapi: bool = False,
        asyncapi_host: str = "0.0.0.0",
        asyncapi_port: int = 8080,
    ) -> None:
        self.force_exit = False
        self.should_exit = False
        self.started = False

        self._handler_cls = Handler
        self._default_handler: Handler | None = None
        self._default_consumer: dict[str, typing.Any] | None = None
        if config:
            self._default_consumer = {
                "config": config,
                "name": name,
            }

        self._consumer_configs: dict[str, dict[str, typing.Any]] = {}
        self._producer_configs: dict[str, dict[str, typing.Any]] = {}
        self._configs_collected = False

        self._tasks: set[asyncio.Task[typing.Any]] = set()
        self._consumers: set[EVKafkaConsumer] = set()
        self._producers: set[EVKafkaProducer] = set()
        self._app_context = AppContext()
        self.middleware = middleware or default_stack
        self.lifespan = lifespan
        self._lifespan_manager = LifespanManager(lifespan)

        self.title = title
        self.version = version
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.asyncapi_schema: str | None = None
        self.expose_asyncapi = expose_asyncapi
        self.asyncapi_host = asyncapi_host
        self.asyncapi_port = asyncapi_port
        self._asyncapi_server: AsyncApiServer | None = None

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

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:  # noqa: ARG002
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

        await self._startup_producers()
        await self._startup_consumers()

        if self.expose_asyncapi:
            self._asyncapi_server = AsyncApiServer(
                self.asyncapi(), host=self.asyncapi_host, port=self.asyncapi_port
            )
            await self._asyncapi_server.start()
        self.started = True

    async def _startup_consumers(self) -> None:
        for config_items in self.consumer_configs.values():
            consumer = EVKafkaConsumer(
                config=config_items["config"],
                messages_cb=config_items["messages_cb"],
            )
            self._consumers.add(consumer)
            self._tasks.add(consumer.startup())

    async def _startup_producers(self) -> None:
        for config_items in self.producer_configs.values():
            producer = EVKafkaProducer(config=config_items["config"])
            config_items["sender"].add_producer_callback(producer)
            self._producers.add(producer)
            await producer.start()

    def _collect_configs(self) -> None:
        if self._default_consumer and self._default_handler:
            self.add_consumer(
                config=self._default_consumer["config"],
                handler=self._default_handler,
                name=self._default_consumer["name"],
            )
        self._configs_collected = True

    @property
    def consumer_configs(self) -> dict[str, dict[str, typing.Any]]:
        if not self._configs_collected:
            self._collect_configs()
        return self._consumer_configs

    @property
    def producer_configs(self) -> dict[str, dict[str, typing.Any]]:
        if not self._configs_collected:
            self._collect_configs()
        return self._producer_configs

    async def main(self) -> None:
        while not self.should_exit:
            for task in self._tasks:
                if task.done():
                    self.should_exit = True
                    break
            await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        logger.info("Shutting down")

        if self.expose_asyncapi and self._asyncapi_server:
            await self._asyncapi_server.stop()

        if self.force_exit:
            return

        await self._shutdown_consumers()
        await self._shutdown_producers()
        await self._lifespan_manager.stop()

    async def _shutdown_consumers(self) -> None:
        await asyncio.gather(*(consumer.shutdown() for consumer in self._consumers))

    async def _shutdown_producers(self) -> None:
        await asyncio.gather(*(producer.stop() for producer in self._producers))

    def event(
        self,
        event_type: str,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Wrapped:
        assert self._default_consumer, (
            f"Event cannot be added because default consumer configuration "
            f'is not passed to "{self.__class__.__name__}()"'
        )

        if self._default_handler is None:
            self._default_handler = self._handler_cls()

        return self._default_handler.event(
            event_type, summary=summary, description=description, tags=tags
        )

    def add_consumer(
        self,
        config: ConsumerConfig,
        handler: HandlerApp,
        name: str | None = None,
    ) -> None:
        if self._configs_collected:
            raise RuntimeError(
                "Cannot add another consumer after an application has started"
            )

        app = handler
        for mv in reversed(self.middleware):
            app = mv.cls(app, **mv.options)

        async def messages_cb(
            message_ctx: MessageCtx,
            consumer_ctx: ConsumerCtx,
            app: HandlerApp = app,
            app_context: AppContext = self._app_context,
        ) -> None:
            context = Context(
                message=message_ctx,
                consumer=consumer_ctx,
                state=app_context.state.copy(),
            )
            return await app(context)

        assert name not in self._consumer_configs, "Consumer names must be unique"
        name = name or str(uuid.uuid4())

        self._consumer_configs[name] = {
            "config": config,
            "handler": handler,
            "messages_cb": messages_cb,
        }

    def add_producer(
        self, config: ProducerConfig, sender: Sender, name: str | None = None
    ) -> None:
        if self._configs_collected:
            raise RuntimeError(
                "Cannot add another producer after an application has started"
            )
        assert name not in self._producer_configs, "Producer names must be unique"
        name = name or str(uuid.uuid4())

        self._producer_configs[name] = {
            "config": config,
            "sender": sender,
        }

    def asyncapi(self) -> str:
        if not self.asyncapi_schema:
            self.asyncapi_schema = get_asyncapi_spec(
                title=self.title,
                version=self.version,
                consumer_configs=self.consumer_configs,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
            )
        return self.asyncapi_schema
