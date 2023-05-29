from abc import ABC, abstractmethod
from typing import Awaitable, Callable

import loguru


class NodeCustomBase(ABC):
    def __init__(
        self,
        node_ip: str,
        unicast: Callable[[str, bytes], Awaitable[None]],
        broadcast: Callable[[bytes], Awaitable[None]],
        log: "loguru.Logger",
    ):
        self.node_ip = node_ip
        self.unicast = unicast
        self.broadcast = broadcast
        self.log = log

    @abstractmethod
    async def main(self):
        pass

    @abstractmethod
    async def on_recv(self, src: str, msg: bytes):
        pass

    # NOTE : on_stop implementation is optional
    def on_stop(self):
        pass
