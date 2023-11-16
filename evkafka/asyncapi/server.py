import logging
from typing import Any

from aiohttp import web

logger = logging.getLogger(__name__)


def get_asyncapi_renderer() -> str:
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <link rel="stylesheet" href="https://unpkg.com/@asyncapi/react-component@latest/styles/default.min.css">
      </head>
      <body>
        <div id="asyncapi"></div>
        <script src="https://unpkg.com/@asyncapi/react-component@latest/browser/standalone/index.js"></script>
        <script>
          AsyncApiStandalone.render({
            schema: {
              url: 'asyncapi.json',
              options: { method: "GET", mode: "cors" },
            },
            config: {
              show: {
                sidebar: true,
              }
            },
          }, document.getElementById('asyncapi'));
        </script>
      </body>
    </html>
    """


class AsyncApiServer:
    def __init__(self, spec: dict[str, Any], host='0.0.0.0', port=8080) -> None:
        self.spec = spec
        self.host = host
        self.port = port

        app = web.Application()
        app.add_routes([
            web.get('/asyncapi.json', self.get_asyncapi_spec),
            web.get('/', self.get_asyncapi_renderer)
        ])

        self.runner = web.AppRunner(app)

    async def start(self) -> None:
        logger.info('Start serving AsyncAPI spec at http://%s:%s', self.host, self.port)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

    async def stop(self) -> None:
        logger.info('Stop serving AsyncAPI')
        await self.runner.cleanup()

    async def get_asyncapi_renderer(self, request: web.Request) -> web.Response:  # noqa: ARG002
        body = get_asyncapi_renderer()
        return web.Response(body=body, content_type="text/html")

    async def get_asyncapi_spec(self, request: web.Request) -> web.Response:  # noqa: ARG002
        return web.Response(body=self.spec, content_type="application/json")
