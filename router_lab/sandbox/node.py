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
        self.thread1 = threading.Thread(target=self.__recv_handler)
        self.thread1.start()

        self.thread2 = threading.Thread(target=self.algo.main)
        self.thread2.start()

        self.log.info("Initialized")

    def __del__(self):
        self.stop()

    def __recv_handler(self):
        while not self.stop_signal.is_set():
            try:
                src_ip, byte1 = self.in_queue.get(timeout=0.5)
                if src_ip != "":
                    self.received_pkts += 1
                    self.received_bytes += len(byte1)
                    threading.Thread(target=self.algo.on_recv, args=(src_ip, byte1)).start()
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                self.log.exception(e)
                break

    def get_node_stats(self) -> NodeStats:
        return NodeStats(
            self.ip,
            self.down,
            self.received_pkts,
            self.sent_pkts,
            self.received_bytes,
            self.sent_bytes,
        )

    def stop(self):
        self.stop_signal.set()
        self.in_queue.put(("", True))
        self.thread1.join()
        # TODO : graceful stop algo thread
        self.algo.on_stop()
