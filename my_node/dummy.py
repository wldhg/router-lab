from router_lab import NodeCustomBase


class DummyNodeImpl(NodeCustomBase):
    # NOTE : every_1s implementation is optional
    async def every_1s(self):
        pass

    # NOTE : main implementation is mandatory
    async def main(self):
        await self.broadcast(b"Hello, world!")

    # NOTE : on_recv implementation is mandatory
    async def on_recv(self, src: str, msg: bytes):
        self.log.info(f"Received from {src}: {msg}")
        if msg == b"Hello, world!":
            await self.unicast(src, b"Hello, " + src.encode() + b"!")

    # NOTE : on_queue implementation is optional
    async def on_queue(self, dst: str, msg: bytes):
        pass

    # NOTE : on_start implementation is optional
    # NOTE : on_start is synchronous (not async)
    def on_start(self):
        self.log.info(f"Node started (${self.ip})")

    # NOTE : on_stop implementation is optional
    # NOTE : on_stop is synchronous (not async)
    def on_stop(self):
        self.log.info(f"Node stopped (${self.ip})")
