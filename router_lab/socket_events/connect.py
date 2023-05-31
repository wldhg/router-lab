from typing import Any, Callable

import loguru

from ..parts import RouterLabParts
from ..sandbox import Sandbox


async def connect(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    sbx = Sandbox(rlp.cfg, rlp.get_main_logger("sbx").bind(sid=sid))
    await rlp.sandboxes.add(sid, sbx)
