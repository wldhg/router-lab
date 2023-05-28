import multiprocessing as mp
import multiprocessing.connection as mpc
import threading
import uuid
from typing import Callable

import loguru

from ..config import RouterLabConfig
from ..utils import ThreadedPromiseLike
from .world import World


class Sandbox:
    def __init__(self, cfg: RouterLabConfig, log: "loguru.Logger"):
        self.__cfg = cfg
        self.__log = log

        self.__recv_channels: dict[str, tuple[threading.Lock, Callable[[dict], None]]] = {}

        self.__thr_must_stop = threading.Event()
        self.__thr1 = threading.Thread(target=self.__pipe_recv_producer)
        self.__thr1.start()

        self.__pipe_from_world, self.__pipe_to_world = mpc.Pipe(duplex=True)
        self.__process: mp.Process = mp.Process(
            target=World, args=(self.__pipe_from_world, self.__pipe_to_world)
        )
        self.__process.start()

    def __del__(self):
        self.__thr_must_stop.set()  # reserve to stop while loop
        self.__pipe_from_world.send(("stop", None))  # rotate while loop by feeding .recv()
        if self.__process.is_alive():
            self.__process.terminate()
            self.__process.join()
        self.__thr1.join()  # join at the last for non-blocking termination

    def __pipe_recv_producer(self):
        while not self.__thr_must_stop.is_set():
            try:
                bomb_id, data = self.__pipe_from_world.recv()
            except EOFError:
                self.__log.error("PIPE from the world is closed")
                break
            if bomb_id in self.__recv_channels:
                lock, consumer = self.__recv_channels.pop(bomb_id)
                consumer(data)
                lock.release()
            else:
                self.__log.warning(f"Unknown bomb_id: {bomb_id}")

    def __pipe_sender(self, fn_name: str, data: dict) -> ThreadedPromiseLike[dict]:
        __bomb_id = str(uuid.uuid4())
        __recv_lock = threading.Lock()
        __recv_lock.acquire()

        __data: dict | None = None

        def __recv_consumer(data: dict):
            nonlocal __data
            __data = data

        self.__recv_channels[__bomb_id] = (__recv_lock, __recv_consumer)

        def __recv_resolver() -> dict:
            with __recv_lock:
                assert __data is not None
                if isinstance(__data, Exception):
                    raise __data
                return __data

        self.__pipe_to_world.send((fn_name, __bomb_id, data))

        return ThreadedPromiseLike(__recv_resolver)

    def configure(
        self,
        node_num: int,
        link_min: int,
        link_max: int,
        kbps_min: float,
        kbps_max: float,
        kbps_std_max: float,
        bit_corrupt_rate: float,
        node_down_rate: float,
    ) -> ThreadedPromiseLike[dict]:
        return self.__pipe_sender(
            "configure",
            {
                "node_num": node_num,
                "link_min": link_min,
                "link_max": link_max,
                "kbps_min": kbps_min,
                "kbps_max": kbps_max,
                "kbps_std_max": kbps_std_max,
                "bit_corrupt_rate": bit_corrupt_rate,
                "node_down_rate": node_down_rate,
            },
        )

    def start(self, algo_path: str):
        self.__pipe_to_world.send(("start", {"algo_path": algo_path}))

    def stop(self):
        self.__pipe_to_world.send(("stop", None))

    def get_stat(self) -> dict[str, str | int | float]:
        raise NotImplementedError

    def is_running(self) -> bool:
        raise NotImplementedError

    def is_configured(self) -> bool:
        raise NotImplementedError
