from dataclasses import dataclass
from typing import Literal

WorldState = Literal["initialized", "configured", "running", "stopped"]


@dataclass
class WorldStats:
    state: WorldState
    transmissions: dict[tuple[str, str, str], int]
    nodes_updown: dict[str, bool]
