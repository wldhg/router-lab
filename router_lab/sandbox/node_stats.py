from dataclasses import dataclass


@dataclass
class NodeStats:
    ip: str
    is_down: bool
    sent_pkts: int
    recv_pkts: int
    sent_bytes: int
    recv_bytes: int
