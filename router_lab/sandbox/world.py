import asyncio
import datetime
import logging.handlers
import multiprocessing.connection as mpc
import queue
import random
import threading
import time
import uuid
from typing import Any

import numpy as np

from ..utils import broadcast_ip, init_logger, random_ip
from .node import Node
from .node_stats import NodeStats
from .world_info import WorldInfo
from .world_logging import WorldLoggingHandler
from .world_stats import WorldState, WorldStats


class World:
    def __init__(self, pipe_to_sbx: mpc.Connection, pipe_from_sbx: mpc.Connection):
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
        self.node_down_interval = 8.88
        self.node_enqueue_rate = 0.01

        self.current_nodes: list[Node] = []
        self.current_links: dict[tuple[str, str], bool]
        self.current_nodes_updown: dict[str, bool] = {}
        self.current_transmissions: dict[tuple[str, str, str], int] = {}
        self.current_transmissions_start_time: dict[tuple[str, str, str], float] = {}
        self.current_mq_to_node: list[queue.Queue] = []
        self.current_thread1: None | threading.Thread = None
        self.current_thread_stop_event = threading.Event()
        self.current_state: WorldState = "initialized"

        self.stat_1hop_latency = 0.0
        self.stat_1hop_throughput = 0.0
        self.stat_packet_sent_bytes = 0.0
        self.stat_packet_sent_count = 0
        self.stat_packet_recv_bytes = 0.0
        self.stat_packet_recv_count = 0
        self.stat_started_at = 0.0
        self.stat_custom: dict[str, tuple[float, float, float, int]] = {}

        self.__initialize()
        self.__pipe_receiver()

    def export_world(self) -> dict[str, Any]:
        # TODO
        # Socket & Sandbox pipeline also needs to be updated
        raise NotImplementedError

    def __initialize(self):
        self.id = str(uuid.uuid4())[:4]
        log_file_name = f"{int(time.time())}-{self.id}.log"
        self.log_buffer = WorldLoggingHandler()
        self.log = init_logger(log_file_name, log_level="DEBUG").bind(world=self.id)
        self.log.add(self.log_buffer, level=logging.DEBUG)
        self.init_time = datetime.datetime.now().timestamp()
        self.log.info(f"World initialized, find your log at logs/{log_file_name} !")
        self.current_state: WorldState = "initialized"
        self.re_initialization_required = False

    def __pipe_action(self, command: str, bomb_id: str, **kwargs: Any):
        try:
            result = getattr(self, command)(**kwargs)
            self.pipe_to_sbx.send((bomb_id, result))
        except Exception as e:
            self.log.error(f"Exception occurred while processing command: {command}")
            self.log.exception(e)
            if self.pipe_to_sbx.closed:
                self.log.error("PIPE to the sandbox is closed")
            else:
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
        link_sparsity: int,
        kbps_min: float,
        kbps_max: float,
        kbps_std_max: float,
        bit_corrupt_rate: float,
        node_down_rate: float,
        node_down_interval: float,
        node_enqueue_rate: float,
    ):
        if self.re_initialization_required:
            self.__initialize()

        node_ips = set()
        while len(node_ips) < node_num:
            node_ips.add(random_ip(subnet))
        self.node_ips = list(node_ips)

        self.subnet = subnet
        self.broadcast_ip = broadcast_ip(subnet)
        self.mtu = mtu

        topo_try = 0
        while True:
            topo_try += 1
            if topo_try % 1000 == 0:
                self.log.warning(f"Failed to generate a valid topology {topo_try} times")
            topo_connection = np.random.randint(0, 2, (node_num, node_num))
            topo_connection = np.triu(topo_connection, 1)
            for _ in range(link_sparsity):
                topo_connection = topo_connection * np.random.randint(0, 2, (node_num, node_num))
                topo_connection = np.triu(topo_connection, 1)
            test_is_all_connected = False
            topo_connection_test = topo_connection.copy()
            topo_connection_test = topo_connection_test | topo_connection_test.T
            for idx in range(node_num):
                topo_connection_test[idx, idx] = True
                for _ in range(node_num):
                    topo_connection_test = topo_connection_test @ topo_connection_test
                if np.all(topo_connection_test):
                    test_is_all_connected = True
                    break
            if test_is_all_connected:
                break

        topo_connection = topo_connection.astype(np.bool_)

        topo_kbps_mean = topo_connection.copy().astype(np.float64)
        topo_kbps_mean *= np.maximum(
            np.ones(topo_kbps_mean.shape) * 0.01,
            np.random.normal(
                (kbps_min + kbps_max) / 2, (kbps_max - kbps_min) / 2.5, topo_kbps_mean.shape
            ),
        )

        topo_kbps_std = topo_connection.copy().astype(np.float64)
        topo_kbps_std *= np.abs(np.random.normal(0, kbps_std_max, topo_kbps_std.shape))

        self.topo = topo_connection | topo_connection.T
        self.kbps_mean = topo_kbps_mean + topo_kbps_mean.T
        self.kbps_std = topo_kbps_std + topo_kbps_std.T
        self.bit_corrupt_rate = bit_corrupt_rate
        self.node_down_rate = node_down_rate
        self.node_down_interval = node_down_interval
        self.node_enqueue_rate = node_enqueue_rate
        self.current_state = "configured"

    def configure_by_import(self, world: dict[str, Any]):
        # TODO
        # Socket & Sandbox pipeline also needs to be updated
        raise NotImplementedError

    def record_world_stat(self, stat_name: str, stat_value: float | int):
        if self.current_state == "running":
            stat_value = float(stat_value)
            if stat_name not in self.stat_custom:
                self.stat_custom[stat_name] = (stat_value, stat_value, stat_value, 1)
            self.stat_custom[stat_name] = (
                (stat_value + self.stat_custom[stat_name][0] * self.stat_custom[stat_name][3])
                / (self.stat_custom[stat_name][3] + 1),
                min(self.stat_custom[stat_name][1], stat_value),
                max(self.stat_custom[stat_name][2], stat_value),
                self.stat_custom[stat_name][3] + 1,
            )

    def start(self, algo_path: str):
        self.log.info(f"Starting world with node implementation: {algo_path}")
        self.current_links = {}
        for ip1 in self.node_ips:
            for ip2 in self.node_ips:
                if ip1 < ip2:
                    self.current_links[(ip1, ip2)] = False
        self.current_mq_to_node = [queue.Queue() for _ in range(len(self.node_ips))]
        self.current_nodes = [
            Node(
                ip,
                algo_path,
                self.current_mq_to_node[idx],
                self.node_enqueue_rate,
                self.unicast,
                self.broadcast,
                self.record_world_stat,
                self.get_random_ip,
                self.log.bind(node=ip),
            )
            for idx, ip in enumerate(self.node_ips)
        ]
        self.current_transmissions = {}
        self.current_transmissions_start_time = {}

        self.current_state = "running"

        self.current_thread_stop_event = threading.Event()
        self.current_thread1 = threading.Thread(target=self.update_node_updown_thread, daemon=True)
        self.current_thread1.start()

        self.stat_1hop_latency = 0.0
        self.stat_1hop_throughput = 0.0
        self.stat_packet_sent_bytes = 0.0
        self.stat_packet_sent_count = 0
        self.stat_packet_recv_bytes = 0.0
        self.stat_packet_recv_count = 0
        self.stat_started_at = datetime.datetime.now().timestamp()
        self.stat_custom = {}

        for node in self.current_nodes:
            node.start()

    def stop(self):
        self.current_state = "stopped"  # this will also stop all transmissions
        self.re_initialization_required = True
        if hasattr(self, "current_nodes"):
            for node in self.current_nodes:
                node.stop()
        self.current_thread_stop_event.set()  # stop node up/down thread
        if self.current_thread1 is not None:
            self.current_thread1.join()
        self.log.info("World stopped")

    def start_activity(self):
        if self.current_state != "running":
            return
        for node in self.current_nodes:
            node.start_activity()

    def update_node_updown_thread(self):
        while not self.current_thread_stop_event.is_set():
            updown = np.random.binomial(1, self.node_down_rate, len(self.node_ips))
            updown_dict = dict(zip(self.node_ips, map(bool, updown)))
            for idx in range(len(self.node_ips)):
                if updown[idx]:
                    self.current_nodes[idx].down = True
                else:
                    self.current_nodes[idx].down = False
            self.current_nodes_updown = updown_dict
            self.log.debug(f"Node U/D updated: {np.sum(updown)} nodes down")
            time.sleep(self.node_down_interval)

    def get_stats(self) -> WorldStats:
        transmissions: list[tuple[str, str, str, int]] = []
        current_transmissions = self.current_transmissions.copy()
        for (src, dst, data_id), count in current_transmissions.items():
            transmissions.append((src, dst, data_id, count))
        custom_stats: dict[str, tuple[float, float, float, int]] = {}
        for stat_name, (stat_mean, stat_min, stat_max, stat_count) in self.stat_custom.items():
            custom_stats[stat_name] = (stat_mean, stat_min, stat_max, stat_count)
        return WorldStats(
            state=self.current_state,
            started_at=self.stat_started_at,
            world_stats=(
                self.stat_packet_sent_bytes,
                self.stat_packet_sent_count,
                self.stat_packet_recv_bytes,
                self.stat_packet_recv_count,
            ),
            world_1hop_latency=self.stat_1hop_latency,
            world_1hop_throughput=self.stat_1hop_throughput,
            transmissions=transmissions,
            nodes_updown=self.current_nodes_updown,
            custom_stats=custom_stats,
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
            self.init_time,
        )

    def get_random_ip(self) -> str:
        return self.node_ips[np.random.randint(0, len(self.node_ips))]

    def get_node_stats(self, ip: dict[str, str]) -> NodeStats:
        idx = self.node_ips.index(ip["ip"])
        return self.current_nodes[idx].get_node_stats()

    def get_logs(self) -> list[dict[str, Any]]:
        logs = [r.__dict__["msg"] for r in self.log_buffer.flush()]
        return logs

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
                await self.unicast(node_src, self.node_ips[dst_idx], data)

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

        ip_tuple = (node_src, node_dst) if node_src < node_dst else (node_dst, node_src)
        assert ip_tuple in self.current_links

        # Exponential Backoff with 1ms slot time
        backoff = 0
        while self.current_links[ip_tuple]:
            backoff += 1
            if backoff > 12:
                return
            await asyncio.sleep(max([random.random() * 0.0005 * 2**backoff, 0.001]))

        self.stat_packet_sent_count += 1
        self.stat_packet_sent_bytes += len(data)

        self.current_links[ip_tuple] = True
        self.current_transmissions[(node_src, node_dst, data_id)] = 0
        self.current_transmissions_start_time[(node_src, node_dst, data_id)] = time.time()
        for _ in range(100):
            if self.current_state == "stopped":
                return
            if self.current_nodes[src_idx].down:
                self.current_links[ip_tuple] = False
                self.current_transmissions.pop((node_src, node_dst, data_id))
                return
            self.current_transmissions[(node_src, node_dst, data_id)] += 1
            await asyncio.sleep(delay)
        self.current_transmissions.pop((node_src, node_dst, data_id))

        if self.current_nodes[dst_idx].down:
            self.current_links[ip_tuple] = False
            return

        self.stat_packet_recv_count += 1
        self.stat_packet_recv_bytes += len(data)

        latency = time.time() - self.current_transmissions_start_time.pop(
            (node_src, node_dst, data_id)
        )
        self.stat_1hop_latency = (
            self.stat_1hop_latency * (self.stat_packet_recv_count - 1) + latency
        ) / self.stat_packet_recv_count
        self.stat_1hop_throughput = (self.stat_packet_recv_bytes) / (
            self.stat_packet_recv_count * self.stat_1hop_latency
        )

        self.current_mq_to_node[dst_idx].put((node_src, data))
        self.current_links[ip_tuple] = False
