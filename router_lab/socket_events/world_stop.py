from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def world_stop(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    # 1. Stop world's, nodes' executions.
    # 2. Stop send subscription data.

    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if not sbx.is_running():
        await send_500("World is not running.")
        return

    sub_tasks = rlp.subscription_tasks.get(sid)
    if sub_tasks is not None:
        for task in sub_tasks:
            task.cancel()
    await rlp.subscription_tasks.remove(sid)

    sbx.stop().once(send_200).catch(send_500)
