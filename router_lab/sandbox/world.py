import asyncio
import multiprocessing.connection as mpc
import queue
import threading
import time
import uuid

import numpy as np

from ..utils import init_logger
from .node import Node


class World:
    def __init__(self, sid: str, pipe_to_sbx: mpc.Connection, pipe_from_sbx: mpc.Connection):
        self.log = init_logger(f"{time.time()}-{sid}.log").bind(env=sid)

        self.pipe_to_sbx = pipe_to_sbx
        self.pipe_from_sbx = pipe_from_sbx

        self.node_names = []
        self.topo = np.zeros((0, 0), dtype=np.bool_)
        self.kbps_mean = np.zeros((0, 0), dtype=np.float64)
        self.kbps_std = np.zeros((0, 0), dtype=np.float64)
        self.bit_corrupt_rate = 0.0001
        self.node_down_rate = 0.01

        self.current_nodes = []
        self.current_nodes_lock = []
        self.current_nodes_lock_global = asyncio.Lock()
        self.current_transmissions = {}
        self.current_mq_to_node = []
        self.current_mq_from_node = []
        self.current_thread1 = None
        self.current_thread2 = None
        self.current_thread_stop_signal = False

        self.log.info("World initialized")
        self.__pipe_receiver()

    def __del__(self):
        self.current_thread_stop_signal = True
        if self.current_thread1 is not None:
            self.current_thread1.join()
        if self.current_thread2 is not None:
            self.current_thread2.join()
        for node in self.current_nodes:
            node.stop()

        self.pipe_to_sbx.send(("", True))

    def __pipe_receiver(self):
        while True:
            try:
                command, bomb_id, kwargs = self.pipe_from_sbx.recv()
            except EOFError:
                break

            if command in self.__dict__:
                try:
                    result = self.__dict__[command](**kwargs)
                    self.log.info(f"Processed command: {command}")
                    self.pipe_to_sbx.send((bomb_id, result))
                except Exception as e:
                    self.log.error(f"Exception occurred while processing {command}: {e}")
                    self.pipe_to_sbx.send((bomb_id, e))

    def configure(
        self,
        node_num: int,
        link_min: int,
        link_max: int,
        kbps_min: float,
        kbps_max: float,
        kbps_std_max: float,
        bit_corrupt_rate: float = 0.0001,
        node_down_rate: float = 0.01,
    ):
        node_names = set()
        while len(node_names) < node_num:
            node_names.add(str(uuid.uuid4())[:4])
        self.node_names = list(node_names)

        while True:
            topo_connection = np.random.randint(0, 2, (node_num, node_num))
            topo_connection = np.triu(topo_connection, 1)
            if link_min <= np.sum(topo_connection) <= link_max:
                break

        topo_connection = topo_connection.astype(np.bool_)

        topo_kbps_mean = topo_connection.copy().astype(np.float64)
        topo_kbps_mean[topo_kbps_mean >= 0] = np.random.normal(
            kbps_min, kbps_max, topo_kbps_mean[topo_kbps_mean >= 0].shape
        )

        topo_kbps_std = topo_connection.copy().astype(np.float64)
        topo_kbps_std[topo_kbps_std >= 0] = np.random.normal(
            0, kbps_std_max, topo_kbps_std[topo_kbps_std >= 0].shape
        )

        self.topo = topo_connection | topo_connection.T
        self.kbps_mean = topo_kbps_mean + topo_kbps_mean.T
        self.kbps_std = topo_kbps_std + topo_kbps_std.T
        self.bit_corrupt_rate = bit_corrupt_rate
        self.node_down_rate = node_down_rate

        self.pipe_to_sbx.send(("env_configured", True))

    def start(self, algo_path: str):
        self.current_nodes_lock = [asyncio.Lock() for _ in range(len(self.node_names))]
        self.current_nodes_lock_global = asyncio.Lock()
        self.current_mq_to_node = [queue.Queue() for _ in range(len(self.node_names))]
        self.current_mq_from_node = [queue.Queue() for _ in range(len(self.node_names))]
        self.current_nodes = [
            Node(
                name,
                algo_path,
                self.current_mq_to_node[idx],
                self.current_mq_from_node[idx],
                self.log,
            )
            for idx, name in enumerate(self.node_names)
        ]
        self.current_transmissions = {}

        self.current_thread_stop_signal = False

        self.current_thread1 = threading.Thread(target=self.update_node_updown_thread, daemon=True)
        self.current_thread1.start()

        self.current_thread2 = threading.Thread(target=self.calculate_metrics, daemon=True)
        self.current_thread2.start()

        self.pipe_to_sbx.send(("env_started", True))

    def update_node_updown_thread(self):
        while not self.current_thread_stop_signal:
            time.sleep(2.5)
            updown = np.random.binomial(1, self.node_down_rate, len(self.node_names))
            for idx in range(len(self.node_names)):
                if updown[idx]:
                    self.current_nodes[idx].down = True
                else:
                    self.current_nodes[idx].down = False
            self.log.info(f"Node U/D updated: {np.sum(updown)} nodes down")

    def calculate_metrics(self):
        raise NotImplementedError

    def apply_corrupt(self, data: bytes) -> bytes:
        data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        corrupt = np.random.binomial(1, self.bit_corrupt_rate, data_bits.shape)
        data_bits = np.logical_xor(data_bits, corrupt)  # only flip bits that are marked as corrupt
        data = np.packbits(data_bits).tobytes()
        return data

    def broadcast(self, node_src: str, data: bytes):
        src_idx = self.node_names.index(node_src)

        for dst_idx in range(len(self.node_names)):
            if self.topo[src_idx, dst_idx]:
                asyncio.run(self.unicast(node_src, self.node_names[dst_idx], data))

    async def unicast(self, node_src: str, node_dst: str, data: bytes):
        src_idx = self.node_names.index(node_src)
        dst_idx = self.node_names.index(node_dst)

        if src_idx == dst_idx:
            return

        if not self.topo[src_idx, dst_idx]:
            return

        data = self.apply_corrupt(data)
        data_id = str(uuid.uuid4())[:4]

        kbps_mean = self.kbps_mean[src_idx, dst_idx]
        kbps_std = self.kbps_std[src_idx, dst_idx]
        kbps = np.random.normal(kbps_mean, kbps_std)
        if kbps < 0.001:
            kbps = 0.001

        bps = kbps * 1000
        delay = len(data) * 8 / bps / 100

        async with self.current_nodes_lock_global:
            async with self.current_nodes_lock[src_idx]:
                self.current_transmissions[(node_src, node_dst, data_id)] = 0
                for _ in range(100):
                    self.current_transmissions[(node_src, node_dst, data_id)] += 1
                    await asyncio.sleep(delay)
                self.current_transmissions.pop((node_src, node_dst, data_id))

                if self.current_nodes[dst_idx].down:
                    return

                self.current_mq_to_node[dst_idx].put((node_src, data_id, data))

                self.log.info(
                    "Sent from {} to {}: {} bytes, {:.2f} kbps, {:.2f} s".format(
                        node_src, node_dst, len(data), kbps, delay
                    )
                )
