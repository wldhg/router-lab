from router_lab import NodeCustomBase


class DummyNodeImpl(NodeCustomBase):
    # NOTE : all functions are optional

    async def every_1s(self):
        pass

    async def main(self):
        await self.broadcast(b"Hello, world!")

    async def on_recv(self, src_1hop: str, data: bytes):
        self.log.info(f"Received from {src_1hop}: {data}")
        if data == b"Hello, world!":
            await self.unicast(src_1hop, b"Hello, " + src_1hop.encode() + b"!")

    async def on_queue(self, dst: str, data: bytes):
        pass

    # NOTE : on_start is synchronous (not async)
    def on_start(self):
        self.log.info(f"Node started (${self.ip})")

    # NOTE : on_stop is synchronous (not async)
    def on_stop(self):
        self.log.info(f"Node stopped (${self.ip})")
