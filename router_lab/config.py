from dataclasses import dataclass


@dataclass
class RouterLabConfig:
    socket_host: str = "localhost"
    socket_port: int = 49699
    socket_ns: str = "/rlab"

    world_stat_interval: float = 0.1
