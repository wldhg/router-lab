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
        get_random_ip: Callable[[], str],
        log: "loguru.Logger",
    ):
        self.ip = node_ip
        self.unicast = unicast
        self.broadcast = broadcast
        self.record_stat = record_stat
        self.record_table = record_table
        self.get_random_ip = get_random_ip
        self.log = log

    async def every_1s(self):
        pass

    async def main(self):
        pass

    async def on_recv(self, src_1hop: str, pkt: bytes):
        pass

    async def on_queue(self, dst: str, pkt: bytes):
        pass

    def on_start(self):
        pass

    def on_stop(self):
        pass
