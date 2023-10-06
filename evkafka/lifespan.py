import asyncio
import logging
import typing
from contextlib import asynccontextmanager

from .types import Lifespan

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _empty_lifespan() -> typing.AsyncIterator[None]:
    yield


class LifespanManager:
    def __init__(
        self,
        lifespan: Lifespan | None,
    ):
        self.lifespan = lifespan or _empty_lifespan
        self.should_exit = False
        self.state: dict[str, typing.Any] = {}

    async def start(self) -> None:
        self._wait_started = asyncio.Event()
        self._shutdown = asyncio.Event()
        self._wait_stopped = asyncio.Event()

        self._task = asyncio.create_task(self.main())
        await self._wait_started.wait()

    async def stop(self) -> None:
        if self.should_exit:
            return

        self._shutdown.set()
        await self._wait_stopped.wait()

    async def main(self) -> None:
        started = False

        try:
            async with self.lifespan() as state:
                if state is not None:
                    self.state = state
                started = True
                self._wait_started.set()

                await self._shutdown.wait()

        except BaseException:
            if not started:
                logger.exception("Error while starting lifespan")
            else:
                logger.exception("Error while shutting down lifespan")

            self.should_exit = True

        finally:
            self._wait_started.set()
            self._wait_stopped.set()
