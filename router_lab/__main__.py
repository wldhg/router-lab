import asyncio
import os
import signal
import sys
from dataclasses import dataclass
from types import FrameType

import aiohttp_cors
import socketio
import typer
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_urldispatcher import Resource
from loguru import logger

from . import socket_events
from .config import RouterLabConfig
from .parts import RouterLabParts
from .utils import __version__, init_logger

app = typer.Typer()


@app.command()
def version():
    typer.echo(f"Router Lab: version {__version__}")


@app.command(name="run")
@dataclass
class RouterLab(RouterLabConfig):
    """Router Lab Backend ❤️"""

    def __post_init__(self):
        init_logger("router_lab.log", self.log_level)

        logger.info("Router Lab Backend! will be on {}:{}", self.socket_host, self.socket_port)

        app = web.Application()
        sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
        sio.attach(app)

        cors = aiohttp_cors.setup(
            app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*",
                )
            },
        )

        parts = RouterLabParts.build(logger, sio, app, self)

        for v in socket_events.__dict__.values():
            try:
                if str(v.__module__).startswith("router_lab.socket_events"):
                    parts.add_sio_event_handler(v)
            except:
                pass

        def rlab_static_path(path: str) -> str:
            path1 = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "web", "html", path)
            )
            path2 = os.path.normpath(os.path.join(os.getcwd(), "web", "html", path))
            if os.path.exists(path1):
                return path1
            return path2

        rlab_handle_log = logger.bind(ctx="web")

        async def rlab_handle(request: Request):
            requested_path = str(request.path)
            if len(requested_path) > 0 and requested_path[0] == "/":
                requested_path = requested_path[1:]

            if requested_path == "":
                requested_path = "index.html"
            elif requested_path.endswith("/"):
                requested_path += "index.html"
                if os.path.exists(rlab_static_path(requested_path)):
                    return web.HTTPFound(requested_path)
                else:
                    return web.HTTPNotFound()

            static_path = rlab_static_path(requested_path)
            if os.path.exists(static_path):
                rlab_handle_log.info(f"Requested: {static_path}")
                return web.FileResponse(static_path)
            else:
                return web.HTTPNotFound()

        resource: Resource = app.router.add_resource("/{tail:.*}")
        resource.add_route("GET", rlab_handle)

        for route in list(app.router.routes()):
            if route.resource:
                if route.resource.canonical != "/socket.io/":
                    cors.add(route)
            else:
                cors.add(route)

        def signal_handler(sig: int, frame: FrameType | None):
            logger.info("Router Lab Backend is shutting down...")
            for task in asyncio.all_tasks():
                task.cancel()
            for key in parts.sandboxes.keys():
                sbx = parts.sandboxes.get(key)
                if sbx is not None:
                    sbx.terminate_process()
                    logger.info(f"Terminated sandbox {key} to shutdown")
            logger.info("Bye!")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        logger.success("Router Lab Backend is ready!")
        try:
            web.run_app(
                app,
                host=self.socket_host,
                port=self.socket_port,
                print=logger.info,
                handle_signals=False,
            )
        except KeyboardInterrupt:
            logger.info("Router Lab Backend is shutting down...")
            asyncio.create_task(parts.sandboxes.destroy())


if __name__ == "__main__":
    app()
