import asyncio
import glob
import os
import threading
import time

import loguru

from ..parts import RouterLabParts
from ..sandbox import Sandbox
from ..utils import make_200, make_500


async def configure(rlp: RouterLabParts, log: "loguru.Logger", sid: str, data: dict):
    log.info(f"Configuring environment: {sid}")

    try:
        assert "node_num" in data, "node_num is required."
        assert "link_min" in data, "link_min is required."
        assert "link_max" in data, "link_max is required."
        assert "kbps_min" in data, "kbps_min is required."
        assert "kbps_max" in data, "kbps_max is required."
        assert "kbps_std_max" in data, "kbps_std_max is required."
    except AssertionError as e:
        await rlp.sio.emit(
            "env_configured",
            make_500(str(e)),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        )
        return

    env_proc = rlp.sandboxes.get(sid)

    if env_proc.is_running():
        await rlp.sio.emit(
            "env_configured",
            make_500("Environment is already running."),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        )
        return

    env_proc.once(
        "env_configured",
        lambda result: await rlp.sio.emit(
            "env_configured",
            make_200({}) if result else make_500("Failed to configure environment."),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        ),
    )

    env_proc.configure(
        data["node_num"],
        data["link_min"],
        data["link_max"],
        data["kbps_min"],
        data["kbps_max"],
        data["kbps_std_max"],
        data.get("bit_corrupt_rate", 0.0001),
        data.get("node_down_rate", 0.01),
    )
