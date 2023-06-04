from dataclasses import dataclass


@dataclass
class WorldInfo:
    id: str
    subnet: str
    mtu: int
    node_ips: list[str]
    topo: list[list[bool]]
    bit_corrupt_rate: float
    node_down_rate: float
    initialized_at: float
