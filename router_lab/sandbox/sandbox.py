import multiprocessing as mp
import multiprocessing.connection as mpc
import threading
import uuid
from typing import Any, Callable

import loguru

from ..config import RouterLabConfig
from ..utils import UNDEFINED, PromiseLike
from .node_stats import NodeStats
from .world import World
from .world_info import WorldInfo
from .world_stats import WorldState, WorldStats


class Sandbox:
    def __init__(self, cfg: RouterLabConfig, log: "loguru.Logger"):
        self.__cfg = cfg
        self.__log = log

        self.__recv_channels: dict[str, tuple[threading.Lock, Callable[[dict], None]]] = {}

        __pipe_from_sbx, self.__pipe_to_world = mpc.Pipe(duplex=False)
        self.__pipe_from_world, __pipe_to_sbx = mpc.Pipe(duplex=False)
        self.__process: mp.Process = mp.Process(
            target=World,
            args=(__pipe_to_sbx, __pipe_from_sbx),
            daemon=True,
        )
        self.__process.start()

        self.__thr_stop_event = threading.Event()
        self.__thr_recv = threading.Thread(target=self.__pipe_recv_producer, daemon=True)
        self.__thr_recv.start()

        self.__process_last_state: WorldState = "initialized"
        self.__process_last_state_changable: bool = True
        self.is_initialized = True

    def __del__(self):
        self.destroy()

    def __pipe_recv_producer(self):
        while not self.__thr_stop_event.is_set():
            bomb_id: str = UNDEFINED
            data: Any = UNDEFINED
            try:
                unpackable = self.__pipe_from_world.recv()
                bomb_id, data = unpackable
                if bomb_id == "stop":
                    break
            except EOFError:
                self.__log.error("PIPE from the world is closed")
                break
            except ConnectionResetError:
                self.__log.error("PIPE from the world is reset (maybe due to destruction)")
                break
            except Exception as e:
                self.__log.exception(e)
            if data != UNDEFINED and bomb_id in self.__recv_channels:
                lock, consumer = self.__recv_channels.pop(bomb_id)
                consumer(data)
                self.__log.debug(f"SBX = lock release try  : {bomb_id} / lock {id(lock)}")
                lock.release()
                self.__log.debug(f"SBX = lock release done : {bomb_id} / lock {id(lock)}")

    def __pipe_sender(self, fn_name: str, data: dict[str, Any]) -> PromiseLike[Any]:
        __bomb_id = str(uuid.uuid4())
        __recv_lock = threading.Lock()

        __data: Any = UNDEFINED

        def __recv_consumer(data: Any):
            nonlocal __data
            __data = data

        self.__recv_channels[__bomb_id] = (__recv_lock, __recv_consumer)
        self.__log.debug(f"SBX = lock acquire try  : {__bomb_id} / lock {id(__recv_lock)}")
        __recv_lock.acquire()
        self.__log.debug(f"SBX = lock acquire done : {__bomb_id} / lock {id(__recv_lock)}")

        def __recv_resolver() -> Any:
            self.__log.debug(f"SBX = lock entered: {__bomb_id} / lock {id(__recv_lock)}")
            with __recv_lock:  # __pipe_recv_producer() will release the lock
                if isinstance(__data, Exception):
                    self.__log.debug(f"SBX = lock exited 1: {__bomb_id} / lock {id(__recv_lock)}")
                    raise __data
                self.__log.debug(f"SBX = lock exited 2: {__bomb_id} / lock {id(__recv_lock)}")
                return __data

        new_promise = PromiseLike(__recv_resolver)
        self.__pipe_to_world.send((fn_name, __bomb_id, data))

        return new_promise

    def destroy(self):
        if hasattr(self, "is_initialized") and self.is_initialized:
            self.__thr_stop_event.set()
            if self.__process.is_alive():
                self.__process.terminate()
                self.__process.join()
            self.__thr_recv.join()

    def terminate_process(self):
        if self.__process.is_alive():
            self.__process.terminate()
            self.__process.join()

    def configure(
        self,
        subnet: str,
        mtu: int,
        node_num: int,
        link_sparsity: int,
        kbps_min: float,
        kbps_max: float,
        kbps_std_max: float,
        bit_corrupt_rate: float,
        node_down_rate: float,
        node_down_interval: float,
        node_enqueue_rate: float,
    ) -> PromiseLike[None]:
        return self.__pipe_sender(
            "configure",
            {
                "subnet": subnet,
                "mtu": mtu,
                "node_num": node_num,
                "link_sparsity": link_sparsity,
                "kbps_min": kbps_min,
                "kbps_max": kbps_max,
                "kbps_std_max": kbps_std_max,
                "bit_corrupt_rate": bit_corrupt_rate,
                "node_down_rate": node_down_rate,
                "node_down_interval": node_down_interval,
                "node_enqueue_rate": node_enqueue_rate,
            },
        )

    def start(self, algo_path: str) -> PromiseLike[None]:
        self.__process_last_state_changable = True
        return self.__pipe_sender("start", {"algo_path": algo_path})

    def start_activity(self) -> PromiseLike[None]:
        return self.__pipe_sender("start_activity", {})

    def stop(self) -> PromiseLike[None]:
        # pre-set local cache
        self.__process_last_state_changable = False
        self.__process_last_state = "stopped"
        return self.__pipe_sender("stop", {})

    def get_stats(self) -> PromiseLike[WorldStats]:
        def update_stats(stat: WorldStats):
            if self.__process_last_state_changable:
                self.__process_last_state = stat.state

        promise = self.__pipe_sender("get_stats", {})
        promise.once(update_stats)
        return promise

    def get_node_stats(self, ip: str) -> PromiseLike[NodeStats]:
        return self.__pipe_sender("get_node_stats", {"ip": ip})

    def get_info(self) -> PromiseLike[WorldInfo]:
        return self.__pipe_sender("get_info", {})

    def get_logs(self) -> PromiseLike[list[dict[str, Any]]]:
        return self.__pipe_sender("get_logs", {})

    def is_running(self) -> bool:
        return self.__process.is_alive() and self.__process_last_state == "running"

    def is_configured(self) -> bool:
        return self.__process.is_alive() and (
            self.__process_last_state == "configured"
            or self.is_running()
            or self.__process_last_state == "stopped"
        )
