import asyncio
from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def subscribe_world_logs(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    async def logget_fn():
        while True:
            try:
                sbx.get_logs().then(send_200).catch(send_500)
            except EOFError:
                break
            await asyncio.sleep(rlp.cfg.world_log_subscribe_interval)

    logs_task = asyncio.create_task(logget_fn())

    def update_fn(orig: None | list[asyncio.Task]):
        if orig is not None:
            return orig + [logs_task]
        return [logs_task]

    await rlp.subscription_tasks.add(sid, update_fn)
