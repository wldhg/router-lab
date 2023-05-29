from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def world_info(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if not sbx.is_configured():
        send_500("World is not configured.")
        return

    sbx.get_info().once(
        lambda info: send_200(info.__dict__),
    ).catch(
        lambda e: send_500(str(e)),
    )
