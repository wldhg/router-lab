from dataclasses import dataclass


@dataclass
class NodeStats:
    ip: str

    sent_pkts: int
    recv_pkts: int
    sent_bytes: int
    recv_bytes: int

    table_cols: list[str]
    table: dict[str, list[str | float | int]]
