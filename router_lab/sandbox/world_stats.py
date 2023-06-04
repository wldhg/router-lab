from dataclasses import dataclass
from typing import Literal

WorldState = Literal["initialized", "configured", "running", "stopped"]


@dataclass
class WorldStats:
    state: WorldState
    started_at: float

    transmissions: list[tuple[str, str, str, int]]
    nodes_updown: dict[str, bool]

    world_1hop_latency: float
    world_1hop_throughput: float
    world_stats: tuple[float, int, float, int]
    custom_stats: dict[str, tuple[float, float, float, int]]
