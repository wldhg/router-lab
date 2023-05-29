import asyncio
import datetime
import logging.handlers
import multiprocessing.connection as mpc
import queue
import threading
import time
import uuid

import loguru
import numpy as np

from ..utils import broadcast_ip, init_logger, random_ip
from .node import Node
from .node_stats import NodeStats
from .world_info import WorldInfo
from .world_logging import WorldLoggingHandler
from .world_stats import WorldState, WorldStats


class World:
    def __init__(self, pipe_to_sbx: mpc.Connection, pipe_from_sbx: mpc.Connection):
        self.id = str(uuid.uuid4())[:4]

        self.log_buffer = WorldLoggingHandler()
        self.log = init_logger(f"{time.time()}-{self.id}.log").bind(world=self.id)
        self.log.add(self.log_buffer, level=logging.DEBUG)

        self.pipe_to_sbx = pipe_to_sbx
        self.pipe_from_sbx = pipe_from_sbx

        self.subnet: str = ""
        self.broadcast_ip: str = ""
        self.mtu: int = 1500
        self.node_ips: list[str] = []
        self.topo = np.zeros((0, 0), dtype=np.bool_)
        self.kbps_mean = np.zeros((0, 0), dtype=np.float64)
        self.kbps_std = np.zeros((0, 0), dtype=np.float64)
        self.bit_corrupt_rate = 0.0001
        self.node_down_rate = 0.01

        self.current_nodes: list[Node] = []
        self.current_nodes_lock: list[asyncio.Lock] = []
        self.current_nodes_lock_global = asyncio.Lock()
        self.current_nodes_updown: dict[str, bool] = {}
        self.current_transmissions: dict[tuple[str, str, str], int] = {}
        self.current_mq_to_node: list[queue.Queue] = []
        self.current_thread1: None | threading.Thread = None
        self.current_thread_stop_signal = False
        self.current_state: WorldState = "initialized"

        self.start_time = datetime.datetime.now()

        self.log.info("World initialized")
        self.__pipe_receiver()

    def __del__(self):
        self.stop()

    def __pipe_action(self, command: str, bomb_id: str, **kwargs: dict):
        try:
            result = self.__dict__[command](**kwargs)
            self.log.info(f"Processed command: {command}")
            self.pipe_to_sbx.send((bomb_id, result))
        except Exception as e:
            self.log.error(f"Exception occurred while processing {command}: {e}")
            self.pipe_to_sbx.send((bomb_id, e))

    def __pipe_receiver(self):
        while True:
            try:
                command, bomb_id, kwargs = self.pipe_from_sbx.recv()
            except EOFError:
                break

            threading.Thread(
                target=self.__pipe_action, args=(command, bomb_id), kwargs=kwargs
            ).start()

    def configure(
        self,
        subnet: str,
        mtu: int,
        node_num: int,
        link_min: int,
        link_max: int,
        kbps_min: float,
        kbps_max: float,
        kbps_std_max: float,
        bit_corrupt_rate: float,
        node_down_rate: float,
    ):
        node_ips = set()
        while len(node_ips) < node_num:
            node_ips.add(random_ip(subnet))
        self.node_ips = list(node_ips)

        self.subnet = subnet
        self.broadcast_ip = broadcast_ip(subnet)
        self.mtu = mtu

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
        self.current_state = "configured"

    def start(self, algo_path: str):
        self.current_nodes_lock = [asyncio.Lock() for _ in range(len(self.node_ips))]
        self.current_nodes_lock_global = asyncio.Lock()
        self.current_mq_to_node = [queue.Queue() for _ in range(len(self.node_ips))]
        self.current_nodes = [
            Node(
                ip,
                algo_path,
                self.current_mq_to_node[idx],
                self.unicast,
                self.broadcast,
                self.log.bind(node=ip),
            )
            for idx, ip in enumerate(self.node_ips)
        ]
        self.current_transmissions = {}

        self.current_state = "running"

        self.current_thread_stop_signal = False
        self.current_thread1 = threading.Thread(target=self.update_node_updown_thread, daemon=True)
        self.current_thread1.start()

    def stop(self):
        self.current_thread_stop_signal = True
        self.pipe_from_sbx.send(("", True))
        if self.current_thread1 is not None:
            self.current_thread1.join()
        for node in self.current_nodes:
            node.stop()
        self.current_state = "stopped"

    def update_node_updown_thread(self):
        while not self.current_thread_stop_signal:
            time.sleep(2.5)
            updown = np.random.binomial(1, self.node_down_rate, len(self.node_ips))
            updown_dict = dict(zip(self.node_ips, map(bool, updown)))
            for idx in range(len(self.node_ips)):
                if updown[idx]:
                    self.current_nodes[idx].down = True
                else:
                    self.current_nodes[idx].down = False
            self.current_nodes_updown = updown_dict
            self.log.info(f"Node U/D updated: {np.sum(updown)} nodes down")

    def get_stats(self) -> WorldStats:
        return WorldStats(
            state=self.current_state,
            transmissions=self.current_transmissions,
            nodes_updown=self.current_nodes_updown,
        )

    def get_info(self) -> WorldInfo:
        return WorldInfo(
            self.id,
            self.subnet,
            self.mtu,
            self.node_ips,
            self.topo.tolist(),
            self.bit_corrupt_rate,
            self.node_down_rate,
            self.start_time,
        )

    def get_node_stats(self, ip: str) -> NodeStats:
        idx = self.node_ips.index(ip)
        return self.current_nodes[idx].get_node_stats()

    def get_logs(self) -> list[loguru.Record]:
        return self.log_buffer.flush()

    def apply_corrupt(self, data: bytes) -> bytes:
        data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        corrupt = np.random.binomial(1, self.bit_corrupt_rate, data_bits.shape)
        data_bits = np.logical_xor(data_bits, corrupt)  # only flip bits that are marked as corrupt
        data = np.packbits(data_bits).tobytes()
        return data

    async def broadcast(self, node_src: str, data: bytes):
        src_idx = self.node_ips.index(node_src)

        for dst_idx in range(len(self.node_ips)):
            if self.topo[src_idx, dst_idx]:
                asyncio.run(self.unicast(node_src, self.node_ips[dst_idx], data))

    async def unicast(self, node_src: str, node_dst: str, data: bytes):
        if node_dst == self.broadcast_ip:
            await self.broadcast(node_src, data)
            return

        src_idx = self.node_ips.index(node_src)
        dst_idx = self.node_ips.index(node_dst)

        if len(data) > self.mtu:
            return

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

        # NOTE : PHY backoff is mocked without delay, by async sleep and loop

        async with self.current_nodes_lock_global:
            async with self.current_nodes_lock[src_idx]:
                self.current_transmissions[(node_src, node_dst, data_id)] = 0
                for _ in range(100):
                    self.current_transmissions[(node_src, node_dst, data_id)] += 1
                    await asyncio.sleep(delay)
                self.current_transmissions.pop((node_src, node_dst, data_id))

                if self.current_nodes[dst_idx].down:
                    return

                self.current_mq_to_node[dst_idx].put((node_src, data))

                self.log.info(
                    "Sent from {} to {}: {} bytes, {:.2f} kbps, {:.2f} s".format(
                        node_src, node_dst, len(data), kbps, delay
                    )
                )
