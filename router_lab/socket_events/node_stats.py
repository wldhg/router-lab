from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def node_stats(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    ip: str | None = get_data("ip")
    if ip is None:
        send_500("ip is required.")
        return

    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if not sbx.is_configured():
        send_500("World is not configured.")
        return

    sbx.get_node_stats(ip).once(
        lambda stat: send_200(stat.__dict__),
    ).catch(
        lambda e: send_500(str(e)),
    )
