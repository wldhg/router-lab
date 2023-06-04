from abc import ABC, abstractmethod
from typing import Awaitable, Callable

import loguru


class NodeCustomBase(ABC):
    def __init__(
        self,
        node_ip: str,
        unicast: Callable[[str, bytes], Awaitable[None]],
        broadcast: Callable[[bytes], Awaitable[None]],
        record_stat: Callable[[str, float | int], None],
        log: "loguru.Logger",
    ):
        self.ip = node_ip
        self.unicast = unicast
        self.broadcast = broadcast
        self.record_stat = record_stat
        self.log = log

    async def every_1s(self):
        pass

    async def every_3s(self):
        pass

    async def every_5s(self):
        pass

    async def every_10s(self):
        pass

    @abstractmethod
    async def main(self):
        pass

    @abstractmethod
    async def on_recv(self, src: str, msg: bytes):
        pass

    # NOTE : on_stop implementation is optional
    def on_stop(self):
        pass
