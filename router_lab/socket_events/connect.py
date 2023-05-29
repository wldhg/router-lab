from typing import Any, Callable

import loguru

from ..parts import RouterLabParts
from ..sandbox import Sandbox


async def connect(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = Sandbox(rlp.cfg, rlp.get_main_logger("sbx").bind(sid=sid))
    rlp.sandboxes.add(sid, sbx)
