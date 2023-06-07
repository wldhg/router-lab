from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def world_start_activity(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if not sbx.is_configured():
        await send_500("World is not configured.")
        return

    if not sbx.is_running():
        await send_500("World is not running.")
        return

    sbx.start_activity().once(send_200).catch(send_500)
