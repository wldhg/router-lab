from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Protocol

import loguru


class RecordStatFnType(Protocol):
    def __call__(self, **stats: float | int) -> None:
        ...


class RecordTableFnType(Protocol):
    def __call__(self, row_name: str, **table: str | float | int) -> None:
        ...


class NodeCustomBase(ABC):
    def __init__(
        self,
        node_ip: str,
        unicast: Callable[[str, bytes], Awaitable[None]],
        broadcast: Callable[[bytes], Awaitable[None]],
        record_stat: RecordStatFnType,
        record_table: RecordTableFnType,
        log: "loguru.Logger",
    ):
        self.ip = node_ip
        self.unicast = unicast
        self.broadcast = broadcast
        self.record_stat = record_stat
        self.record_table = record_table
        self.log = log

    async def every_1s(self):
        pass

    @abstractmethod
    async def main(self):
        pass

    @abstractmethod
    async def on_recv(self, src: str, msg: bytes):
        pass

    async def on_queue(self, dst: str, msg: bytes):
        pass

    def on_start(self):
        pass

    def on_stop(self):
        pass
