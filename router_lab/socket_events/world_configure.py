from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def world_configure(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    data: dict = get_data("data")

    try:
        assert "node_num" in data, "node_num is required."
        assert "link_sparsity" in data, "link_sparsity is required."
        assert "kbps_min" in data, "kbps_min is required."
        assert "kbps_max" in data, "kbps_max is required."
        assert "kbps_std_max" in data, "kbps_std_max is required."
        assert "bit_corrupt_rate" in data, "bit_corrupt_rate is required."
        assert "node_down_rate" in data, "node_down_rate is required."
        assert "node_enqueue_rate" in data, "node_enqueue_rate is required."
    except AssertionError as e:
        await send_500(str(e))
        return

    sbx = rlp.sandboxes.get(sid)
    assert sbx is not None, "Sandbox not found."

    if sbx.is_running():
        await send_500("World is already running.")
        return

    sbx.configure(
        rlp.cfg.world_subnet,
        rlp.cfg.world_mtu,
        data["node_num"],
        data["link_sparsity"],
        data["kbps_min"],
        data["kbps_max"],
        data["kbps_std_max"],
        data["bit_corrupt_rate"],
        data["node_down_rate"],
        rlp.cfg.world_node_down_interval,
        data["node_enqueue_rate"],
    ).once(send_200).catch(send_500)
