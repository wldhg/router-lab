from dataclasses import dataclass
from threading import Thread
from typing import Any, Callable

import loguru
import socketio
from aiohttp import web

from .config import RouterLabConfig
from .sandbox import Sandbox
from .utils import ExplicitDelDict, __version__


@dataclass
class RouterLabParts:
    cfg: RouterLabConfig
    sio: socketio.AsyncServer
    app: web.Application

    sandboxes: ExplicitDelDict[str, Sandbox]
    stat_thrs: ExplicitDelDict[str, Thread]

    _bare_logger: "loguru.Logger"
    _is_built: bool = False

    def __post_init__(self):
        assert self._is_built, "RouterLabParts must be built by RouterLabParts.build()"

    def get_main_logger(self, ctx: str) -> "loguru.Logger":
        """NOTE : explicitly bind context string to the logger"""
        return self._bare_logger.bind(ctx=ctx)

    def add_sio_event_handler(self, handler: Callable[..., Any]):
        def wrapped_handler(
            sid: str, *args, **kwargs  # pyright: ignore[reportMissingParameterType]
        ):
            return handler(
                self,
                self.get_main_logger(f"+{handler.__name__}").bind(sid=sid),
                sid,
                *args,
                **kwargs,
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
            sandboxes=ExplicitDelDict(),
            stat_thrs=ExplicitDelDict(),
            _bare_logger=log,
            _is_built=True,
        )
