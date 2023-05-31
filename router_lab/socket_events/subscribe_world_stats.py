import asyncio
from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def subscribe_world_stats(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    async def stat_fn():
        while True:
            try:
                sbx.get_stats().then(send_200).catch(send_500)
            except EOFError:
                break
            await asyncio.sleep(rlp.cfg.world_stats_subscribe_interval)

    stat_task = asyncio.create_task(stat_fn())

    def update_fn(orig: None | list[asyncio.Task]):
        if orig is not None:
            return orig + [stat_task]
        return [stat_task]

    await rlp.subscription_tasks.add(sid, update_fn)
