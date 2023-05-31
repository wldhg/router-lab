from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def node_stats(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    ip: str | None = get_data("ip")
    if ip is None:
        await send_500("ip is required.")
        return

    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if not sbx.is_configured():
        send_500("World is not configured.")
        return

    sbx.get_node_stats(ip).once(send_200).catch(send_500)
