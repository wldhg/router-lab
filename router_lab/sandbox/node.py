import asyncio
import importlib
import inspect
import os
import queue
import random
import sys
import threading
import time
from typing import Awaitable, Callable

import loguru
import lorem

from .node_custom_base import NodeCustomBase
from .node_stats import NodeStats


class Node:
    def __init__(
        self,
        ip: str,
        algo_path: str,
        in_queue: queue.Queue,
        enqueue_rate: float,
        unicast: Callable[[str, str, bytes], Awaitable[None]],
        broadcast: Callable[[str, bytes], Awaitable[None]],
        record_world_stat: Callable[[str, float | int], None],
        get_random_ip: Callable[[], str],
        logger: "loguru.Logger",
    ):
        self.ip = ip
        self.log = logger.bind(ctx=f"node:{ip}")
        self.down = False
        self.in_queue = in_queue
        self.enqueue_rate = enqueue_rate

        self.is_active = False
        self.is_running = False

        self.received_pkts = 0
        self.sent_pkts = 0
        self.received_bytes = 0
        self.sent_bytes = 0
        self.table: dict[str, dict[str, str | float | int]] = {}
        self.table_cols: set[str] = set()

        def local_unicast(dst: str, msg: bytes) -> Awaitable[None]:
            if self.down:
                return asyncio.sleep(0)
            self.sent_pkts += 1
            self.sent_bytes += len(msg)
            return unicast(ip, dst, msg)

        def local_broadcast(msg: bytes) -> Awaitable[None]:
            if self.down:
                return asyncio.sleep(0)
            self.sent_pkts += 1
            self.sent_bytes += len(msg)
            return broadcast(ip, msg)

        def record_stat(**stats: float | int) -> None:
            for k in stats.keys():
                assert isinstance(k, str), "Key must be string"
                record_world_stat(k, stats[k])

        def record_table(row_name: str, **table: str | float | int) -> None:
            for k in table.keys():
                assert isinstance(k, str), "Key must be string"
                self.table_cols.add(k)
            self.table[row_name] = table

        algo_class: None | type[NodeCustomBase] = None
        algo_module = f"my_node.{os.path.basename(algo_path).replace('.py', '')}"
        if algo_module in sys.modules:
            for v in importlib.reload(sys.modules[algo_module]).__dict__.values():
                if (
                    inspect.isclass(v)
                    and (not inspect.isabstract(v))
                    and (v is not NodeCustomBase)
                    and issubclass(v, NodeCustomBase)
                ):
                    algo_class = v
                    break
        else:
            for v in importlib.import_module(algo_module).__dict__.values():
                if (
                    inspect.isclass(v)
                    and (not inspect.isabstract(v))
                    and (v is not NodeCustomBase)
                    and issubclass(v, NodeCustomBase)
                ):
                    algo_class = v
                    break
        assert algo_class is not None, "No algorithm class found"
        self.algo_class = algo_class
        self.algo: NodeCustomBase = self.algo_class(
            ip,
            local_unicast,
            local_broadcast,
            record_stat,
            record_table,
            self.log,
        )

        self.get_random_ip = get_random_ip

        self.stop_signal = threading.Event()
        self.recv_thr = threading.Thread(target=self.__recv_handler)
        self.recv_thr.start()

    def __del__(self):
        self.stop()

    def __every_handler(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            self.every_1s_task = loop.create_task(self.__every_1s_handler())
            loop.run_until_complete(self.every_1s_task)
        except Exception as e:
            self.log.error(e)
            self.log.exception(e)

    def __main_handler(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            self.main_task = loop.create_task(self.algo.main())
            loop.run_until_complete(self.main_task)
        except Exception as e:
            self.log.error(e)
            self.log.exception(e)

    def __recv_handler(self):
        while not self.stop_signal.is_set():
            try:
                src_ip, byte1 = self.in_queue.get(timeout=0.5)
                if src_ip != "":
                    self.received_pkts += 1
                    self.received_bytes += len(byte1)
                    threading.Thread(target=self.__on_recv_handler, args=(src_ip, byte1)).start()
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                self.log.exception(e)

    def __on_recv_handler(self, src_ip: str, byte1: bytes):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.algo.on_recv(src_ip, byte1))
        except Exception as e:
            self.log.error(e)
            self.log.exception(e)

    async def __every_1s_handler(self):
        while True:
            await asyncio.sleep(1)
            try:
                await self.algo.every_1s()
            except Exception as e:
                self.log.exception(e)

    def get_node_stats(self) -> NodeStats:
        table_cols_list: list[str] = list(self.table_cols)
        table: dict[str, list[str | float | int]] = {}
        for row_name in self.table:
            table[row_name] = [self.table[row_name].get(k, "") for k in table_cols_list]
        return NodeStats(
            self.ip,
            self.sent_pkts,
            self.received_pkts,
            self.sent_bytes,
            self.received_bytes,
            table_cols_list,
            table,
        )

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.algo.on_start()
        threading.Thread(target=self.__every_handler).start()
        threading.Thread(target=self.__main_handler).start()

    async def activity(self):
        self.log.info(f"Node activity started (${self.ip})")
        while True:
            await asyncio.sleep(0.5)
            try:
                prob = random.random() <= self.enqueue_rate
                if prob:
                    dst_ip = self.get_random_ip()
                    if dst_ip != "":
                        await self.algo.on_queue(dst_ip, lorem.sentence().encode())
            except Exception as e:
                self.log.exception(e)

    def __activity_handler(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            self.activity_task = loop.create_task(self.activity())
            loop.run_until_complete(self.activity_task)
        except Exception as e:
            self.log.exception(e)

    def start_activity(self):
        if not self.is_active:
            self.is_active = True
            threading.Thread(target=self.__activity_handler).start()

    def stop(self):
        if hasattr(self, "stop_signal"):
            self.stop_signal.set()
        if hasattr(self, "in_queue"):
            self.in_queue.put(("", True))
        if hasattr(self, "recv_thr"):
            self.recv_thr.join()
        if hasattr(self, "activity_task"):
            if not self.activity_task.done():
                self.activity_task.cancel()
        if hasattr(self, "every_1s_task"):
            if not self.every_1s_task.done():
                self.every_1s_task.cancel()
        if hasattr(self, "main_task"):
            if not self.main_task.done():
                self.main_task.cancel()
        if hasattr(self, "algo"):
            self.algo.on_stop()
