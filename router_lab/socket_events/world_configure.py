from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def world_configure(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    data: dict = get_data("data")

    try:
        assert "node_num" in data, "node_num is required."
        assert "link_min" in data, "link_min is required."
        assert "link_max" in data, "link_max is required."
        assert "kbps_min" in data, "kbps_min is required."
        assert "kbps_max" in data, "kbps_max is required."
        assert "kbps_std_max" in data, "kbps_std_max is required."
    except AssertionError as e:
        send_500(str(e))
        return

    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if sbx.is_running():
        send_500("World is already running.")
        return

    sbx.configure(
        rlp.cfg.world_subnet,
        rlp.cfg.world_mtu,
        data["node_num"],
        data["link_min"],
        data["link_max"],
        data["kbps_min"],
        data["kbps_max"],
        data["kbps_std_max"],
        data.get("bit_corrupt_rate", 0.0001),
        data.get("node_down_rate", 0.01),
    ).once(
        lambda _: send_200({}),
    ).catch(
        lambda e: send_500(str(e)),
    )
