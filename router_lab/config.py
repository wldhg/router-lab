from dataclasses import dataclass


@dataclass
class RouterLabConfig:
    socket_host: str = "localhost"
    socket_port: int = 49699
    socket_ns: str = "/rlab"

    world_stats_subscribe_interval: float = 0.1
    world_log_subscribe_interval: float = 0.1
    world_log_buffer_capacity: int = 2048
    world_subnet: str = "10.0.0.0/8"
    world_mtu: int = 1500
