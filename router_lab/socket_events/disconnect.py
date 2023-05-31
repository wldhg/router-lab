from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def disconnect(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = rlp.sandboxes.get(sid)
    if sbx is not None:
        sbx.destroy()
    await rlp.sandboxes.remove(sid)

    sub_tasks = rlp.subscription_tasks.get(sid)
    if sub_tasks is not None:
        for task in sub_tasks:
            task.cancel()
    await rlp.subscription_tasks.remove(sid)
