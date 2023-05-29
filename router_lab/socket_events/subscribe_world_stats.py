import asyncio
import threading
import time
from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def subscribe_world_stats(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    def stat_fn():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        event = rlp.subscribe_thrs_stop_event.get(sid)
        while event is not None and not event.is_set():
            try:
                sbx.get_stats().then(lambda l: send_200(l.__dict__)).catch(
                    lambda e: send_500(str(e))
                )
            except EOFError:
                break
            time.sleep(rlp.cfg.world_stats_subscribe_interval)
        loop.close()

    stat_thr = threading.Thread(target=stat_fn)
    stat_thr.start()

    def update_fn(orig: None | list[threading.Thread]):
        if orig is not None:
            return orig + [stat_thr]
        return [stat_thr]

    rlp.subscribe_thrs.add(sid, update_fn)
