import time
from dataclasses import dataclass

from router_lab import NodeCustomBase


@dataclass
class DummyPacket:
    src: str  # source ip
    dst: str  # destination ip
    msg: str  # message
    timestamp: float  # timestamp

    def to_bytes(self):
        return (
            self.src.encode()
            + b"\x00"
            + self.dst.encode()
            + b"\x00"
            + self.msg.encode()
            + b"\x00"
            + str(self.timestamp).encode()
        )

    @staticmethod
    def from_bytes(b: bytes):
        src, b = b.split(b"\x00", 1)
        dst, b = b.split(b"\x00", 1)
        msg, b = b.split(b"\x00", 1)
        timestamp = float(b)
        return DummyPacket(src.decode(), dst.decode(), msg.decode(), timestamp)


class DummyNodeImpl(NodeCustomBase):
    async def main(self):
        pkt_bytes = DummyPacket(self.ip, "10.255.255.255", "Hello, world!", time.time()).to_bytes()
        await self.broadcast(pkt_bytes)

    async def on_recv(self, src: str, pkt_bytes: bytes):
        pkt = DummyPacket.from_bytes(pkt_bytes)
        latency = time.time() - pkt.timestamp
        self.record_stat("latency", latency)
        self.log.info(f"Received from {src}: {pkt.msg} (latency: {latency:.3f}s)")
        if pkt.msg == "Hello, world!":
            reply_pkt_bytes = DummyPacket(
                self.ip, pkt.src, "Hello, " + pkt.src + "!", time.time()
            ).to_bytes()
            await self.unicast(src, reply_pkt_bytes)
