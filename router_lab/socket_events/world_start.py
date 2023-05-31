from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def world_start(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    data: dict | None = get_data("data")
    if data is None:
        await send_500("algo is required [parent].")
        return

    if "algo" not in data:
        await send_500("algo is required.")
        return

    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if not sbx.is_configured():
        await send_500("World is not configured.")
        return

    if sbx.is_running():
        await send_500("World is already running.")
        return

    sbx.start(data["algo"]).once(send_200).catch(send_500)
