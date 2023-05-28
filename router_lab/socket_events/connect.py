import asyncio
import glob
import os
import threading
import time

import loguru

from ..parts import RouterLabParts
from ..sandbox import Sandbox
from ..utils import make_200


async def connect(rlp: RouterLabParts, log: "loguru.Logger", sid: str):
    sbx = Sandbox(sid, rlp.cfg, rlp.get_main_logger("sbx").bind(sid=sid))
    rlp.sandboxes.add(sid, sbx)

    await rlp.sio.emit("env_created", make_200({}), room=sid, namespace=rlp.cfg.socket_ns)

    def stat_fn():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            try:
                stats = sbx.get_stat()
                loop.run_until_complete(
                    rlp.sio.emit(
                        "env_stat",
                        make_200({"stats": stats}),
                        room=sid,
                        namespace=rlp.cfg.socket_ns,
                    )
                )
            except EOFError:
                break
            time.sleep(rlp.cfg.env_stat_interval)
        loop.close()

    stat_thr = threading.Thread(target=stat_fn)
    stat_thr.start()

    rlp.stat_thrs.add(sid, stat_thr)
