import asyncio


class TestConsumer:
    def __init__(self, config, messages_cb) -> None:
        self.config = config
        self.messages_cb = messages_cb
        self._shutdown = asyncio.get_running_loop().create_future()
        self._main_loop = None
        self.error = False

    def startup(self):
        self._main_loop = asyncio.create_task(self.run())
        return self._main_loop

    async def run(self) -> None:
        while not self._shutdown.done():
            if self.error:
                raise Exception
            await asyncio.sleep(0.01)

    async def shutdown(self) -> None:
        if self._shutdown.done():
            return
        self._shutdown.set_result(None)
        await asyncio.wait([self._main_loop])
