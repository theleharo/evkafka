import socket
from contextlib import closing

import aiohttp
import pytest

from evkafka.asyncapi.server import AsyncApiServer, get_asyncapi_renderer


@pytest.fixture()
def port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@pytest.fixture()
async def server(port):
    server = AsyncApiServer('{"a":"b"}', host="localhost", port=port)
    await server.start()

    yield server

    await server.stop()


@pytest.mark.usefixtures("server")
async def test_asyncapi_server_returns_renderer(port):
    async with aiohttp.ClientSession() as s:
        async with s.get(f"http://localhost:{port}/") as resp:
            assert resp.status == 200
            assert (await resp.text()) == get_asyncapi_renderer()


@pytest.mark.usefixtures("server")
async def test_asyncapi_server_returns_spec(port):
    async with aiohttp.ClientSession() as s:
        async with s.get(f"http://localhost:{port}/asyncapi.json") as resp:
            assert resp.status == 200
            assert (await resp.json()) == {"a": "b"}
