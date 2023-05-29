import glob
import os
from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def list_impls(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "my_node")
    pys = glob.glob(os.path.join(base_dir, "*.py"))
    algo_candidates = []
    for py in pys:
        basename = os.path.basename(py)
        if basename.startswith("_"):
            continue
        algo_candidates.append(basename)
    send_200({"files": algo_candidates})
