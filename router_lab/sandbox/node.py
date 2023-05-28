import importlib
import inspect
import os
import queue
import threading
import time

import loguru

from algo_my import RLabAlgoBase


class Node:
    def __init__(
        self,
        name: str,
        algo_path: str,
        in_queue: queue.Queue,
        out_queue: queue.Queue,
        logger: "loguru.Logger",
    ):
        self.name = name
        self.log = logger.bind(ctx=f"node:{name}")

        algo_class: None | type[RLabAlgoBase] = None
        for v in importlib.import_module(
            f"algo_my.{os.path.basename(algo_path).replace('.py', '')}"
        ).__dict__.values():
            if (
                inspect.isclass(v)
                and (not inspect.isabstract(v))
                and (v is not RLabAlgoBase)
                and issubclass(v, RLabAlgoBase)
            ):
                algo_class = v
                break

        assert algo_class is not None, "No algorithm class found"
        self.algo_class = algo_class
        self.algo: None | RLabAlgoBase = None

        self.down = False

        self.in_queue = in_queue
        self.out_queue = out_queue

        self.log.info("Initialized")

        self.thread = threading.Thread(target=self.recv_handler)
        self.thread.start()

    def recv_handler(self):
        self.algo = self.algo_class()
        self.log.info("Started")
        while True:
            try:
                byte1 = self.in_queue.get(timeout=0.1)
                self.log.info(f"Got: {byte1}")
                raise NotImplementedError
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                self.log.exception(e)
                break

    def send(self, target: str, msg: bytes):
        self.log.info(f"Sent: {msg}")
        self.out_queue.put((target, msg))

    def stop(self):
        self.log.info("Stopped")
        raise NotImplementedError
