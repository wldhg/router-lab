import asyncio
import glob
import os
import threading
import time

import loguru

from ..parts import RouterLabParts
from ..sandbox import Sandbox
from ..utils import make_200, make_500


async def connect(rlp: RouterLabParts, log: "loguru.Logger", sid: str):
    log.info(f"Connected: {sid}")

    env_proc = EnvProcess(sid, rlp.cfg, rlp.get_main_logger("env_proc").bind(sid=sid))
    rlp.sandboxes.add(sid, env_proc)

    await rlp.sio.emit("env_created", make_200({}), room=sid, namespace=rlp.cfg.socket_ns)

    def stat_fn():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            try:
                stats = env_proc.get_stat()
                loop.run_until_complete(
                    rlp.sio.emit(
                        "env_stat",
                        make_200({"stats": stats}),
                        room=sid,
                        namespace=rlp.cfg.socket_ns,
                    )
                )
            except EOFError:
                break
            time.sleep(rlp.cfg.env_stat_interval)
        loop.close()

    stat_thr = threading.Thread(target=stat_fn)
    stat_thr.start()

    rlp.stat_thrs.add(sid, stat_thr)


async def configure_env(rlp: RouterLabParts, log: "loguru.Logger", sid: str, data: dict):
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


async def get_algo_candidates(rlp: RouterLabParts, log: "loguru.Logger", sid: str):
    base_dir = os.path.join(os.path.dirname(__file__), "..", "algo_my")
    pys = glob.glob(os.path.join(base_dir, "*.py"))
    algo_candidates = []
    for py in pys:
        algo_candidates.append(os.path.basename(py))
    await rlp.sio.emit(
        "get_algo_candidates",
        make_200({"files": algo_candidates}),
        room=sid,
        namespace=rlp.cfg.socket_ns,
    )


async def start_env(rlp: RouterLabParts, log: "loguru.Logger", sid: str, data: dict):
    log.info(f"Starting environment: {sid}")

    try:
        assert "algo" in data, "algo is required."
    except AssertionError as e:
        await rlp.sio.emit(
            "general_error",
            make_500(str(e)),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        )
        return

    env_proc = rlp.sandboxes.get(sid)

    if not env_proc.is_configured():
        await rlp.sio.emit(
            "general_error",
            make_500("Environment is not configured."),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        )
        return

    if env_proc.is_running():
        await rlp.sio.emit(
            "prepared",
            make_500("Environment is already running."),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        )
        return

    env_proc.once(
        "env_started",
        lambda result: await rlp.sio.emit(
            "env_started",
            make_200({}) if result else make_500("Failed to start environment."),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        ),
    )

    env_proc.start(data["algo"])


async def stop_env(rlp: RouterLabParts, log: "loguru.Logger", sid: str):
    log.info(f"Stopping environment: {sid}")

    env_proc = rlp.sandboxes.get(sid)

    if not env_proc.is_running():
        await rlp.sio.emit(
            "prepared",
            make_500("Environment is not running."),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        )
        return

    env_proc.once(
        "env_stopped",
        lambda result: await rlp.sio.emit(
            "env_stopped",
            make_200({}) if result else make_500("Failed to stop environment."),
            room=sid,
            namespace=rlp.cfg.socket_ns,
        ),
    )

    env_proc.stop()


async def disconnect(rlp: RouterLabParts, log: "loguru.Logger", sid: str):
    log.info(f"Disconnected: {sid}")
    rlp.sandboxes.remove(sid)
    rlp.stat_thrs.remove(sid)
