import asyncio
import importlib
import inspect
import os
import queue
import threading
import time
from typing import Awaitable, Callable

import loguru

from .node_custom_base import NodeCustomBase
from .node_stats import NodeStats


class Node:
    def __init__(
        self,
        ip: str,
        algo_path: str,
        in_queue: queue.Queue,
        unicast: Callable[[str, str, bytes], Awaitable[None]],
        broadcast: Callable[[str, bytes], Awaitable[None]],
        logger: "loguru.Logger",
    ):
        self.ip = ip
        self.log = logger.bind(ctx=f"node:{ip}")
        self.down = False
        self.in_queue = in_queue

        self.received_pkts = 0
        self.sent_pkts = 0
        self.received_bytes = 0
        self.sent_bytes = 0

        def local_unicast(dst: str, msg: bytes):
            self.sent_pkts += 1
            self.sent_bytes += len(msg)
            return unicast(ip, dst, msg)

        def local_broadcast(msg: bytes):
            self.sent_pkts += 1
            self.sent_bytes += len(msg)
            return broadcast(ip, msg)

        algo_class: None | type[NodeCustomBase] = None
        for v in importlib.import_module(
            f"my_node.{os.path.basename(algo_path).replace('.py', '')}"
        ).__dict__.values():
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
            self.log,
        )

        self.stop_signal = threading.Event()
        self.recv_thr = threading.Thread(target=self.__recv_handler)
        self.recv_thr.start()

        self.log.info(f"A node initialized - {ip}")

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
            self.every_3s_task = loop.create_task(self.__every_3s_handler())
            self.every_5s_task = loop.create_task(self.__every_5s_handler())
            self.every_10s_task = loop.create_task(self.__every_10s_handler())
            self.every_30s_task = loop.create_task(self.__every_30s_handler())
            loop.run_until_complete(self.every_30s_task)
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

    async def __every_3s_handler(self):
        while True:
            await asyncio.sleep(3)
            try:
                await self.algo.every_3s()
            except Exception as e:
                self.log.exception(e)

    async def __every_5s_handler(self):
        while True:
            await asyncio.sleep(5)
            try:
                await self.algo.every_5s()
            except Exception as e:
                self.log.exception(e)

    async def __every_10s_handler(self):
        while True:
            await asyncio.sleep(10)
            try:
                await self.algo.every_10s()
            except Exception as e:
                self.log.exception(e)

    async def __every_30s_handler(self):
        while True:
            await asyncio.sleep(30)
            try:
                await self.algo.every_30s()
            except Exception as e:
                self.log.exception(e)

    def get_node_stats(self) -> NodeStats:
        return NodeStats(
            self.ip,
            self.down,
            self.received_pkts,
            self.sent_pkts,
            self.received_bytes,
            self.sent_bytes,
        )

    def start(self):
        threading.Thread(target=self.__every_handler).start()
        threading.Thread(target=self.__main_handler).start()

    def stop(self):
        if hasattr(self, "stop_signal"):
            self.stop_signal.set()
        if hasattr(self, "in_queue"):
            self.in_queue.put(("", True))
        if hasattr(self, "recv_thr"):
            self.recv_thr.join()
        if hasattr(self, "every_1s_task"):
            self.every_1s_task.cancel()
        if hasattr(self, "every_3s_task"):
            self.every_3s_task.cancel()
        if hasattr(self, "every_5s_task"):
            self.every_5s_task.cancel()
        if hasattr(self, "every_10s_task"):
            self.every_10s_task.cancel()
        if hasattr(self, "every_30s_task"):
            self.every_30s_task.cancel()
        if hasattr(self, "main_task"):
            if not self.main_task.done():
                self.main_task.cancel()
        if hasattr(self, "algo"):
            self.algo.on_stop()
