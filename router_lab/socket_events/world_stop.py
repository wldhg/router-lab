from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def world_stop(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if not sbx.is_running():
        send_500("World is not running.")
        return

    sbx.stop().once(
        lambda _: send_200({}),
    ).catch(
        lambda e: send_500(str(e)),
    )
