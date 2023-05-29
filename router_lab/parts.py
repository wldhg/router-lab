from dataclasses import dataclass
from threading import Event, Thread
from typing import Any, Awaitable, Callable

import loguru
import socketio
from aiohttp import web

from .config import RouterLabConfig
from .sandbox import Sandbox
from .utils import ExplicitDelDict, __version__, make_200, make_500


@dataclass
class RouterLabParts:
    cfg: RouterLabConfig
    sio: socketio.AsyncServer
    app: web.Application

    sandboxes: ExplicitDelDict[str, Sandbox]
    subscribe_thrs: ExplicitDelDict[str, list[Thread]]
    subscribe_thrs_stop_event: ExplicitDelDict[str, Event]

    _bare_logger: "loguru.Logger"
    _is_built: bool = False

    def __post_init__(self):
        assert self._is_built, "RouterLabParts must be built by RouterLabParts.build()"

    def get_main_logger(self, ctx: str) -> "loguru.Logger":
        """NOTE : explicitly bind context string to the logger"""
        return self._bare_logger.bind(ctx=ctx)

    def add_sio_event_handler(self, handler: Callable[..., Awaitable[Any]]):
        async def wrapped_handler(
            sid: str, *args, **kwargs  # pyright: ignore[reportMissingParameterType]
        ):
            def send_200(data: dict):
                return self.sio.emit(
                    handler.__name__, make_200(data), room=sid, namespace=self.cfg.socket_ns
                )

            def send_500(msg: str):
                return self.sio.emit(
                    handler.__name__, make_500(msg), room=sid, namespace=self.cfg.socket_ns
                )

            def get_data(name: str) -> Any:
                if name in kwargs:
                    return kwargs[name]
                if len(args) > 0:
                    return args[0]
                return None

            await handler(
                self,
                self.get_main_logger(f"+{handler.__name__}").bind(sid=sid),
                send_200,
                send_500,
                get_data,
                sid,
            )

        self.sio.on(handler.__name__, wrapped_handler, self.cfg.socket_ns)
        self._bare_logger.info(f"Socket handler registered: {handler.__name__}")

    @staticmethod
    def build(
        log: "loguru.Logger", sio: socketio.AsyncServer, app: web.Application, cfg: RouterLabConfig
    ) -> "RouterLabParts":
        return RouterLabParts(
            cfg=cfg,
            sio=sio,
            app=app,
            sandboxes=ExplicitDelDict("sandboxes"),
            subscribe_thrs=ExplicitDelDict("subscribe_thrs"),
            subscribe_thrs_stop_event=ExplicitDelDict("subscribe_thrs_stop_event"),
            _bare_logger=log,
            _is_built=True,
        )
