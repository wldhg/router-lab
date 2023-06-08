import glob
import os
from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def list_impls(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[Any], Any],
    send_500: Callable[[Any], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    base_dir1 = os.path.join(os.path.dirname(__file__), "..", "..", "my_node")
    pys1 = glob.glob(os.path.join(base_dir1, "*.py"))
    base_dir2 = os.path.join(os.getcwd(), "my_node")
    pys2 = glob.glob(os.path.join(base_dir2, "*.py"))
    algo_candidates = []
    for py in pys1:
        basename = os.path.basename(py)
        if basename.startswith("_"):
            continue
        algo_candidates.append(basename)
    for py in pys2:
        basename = os.path.basename(py)
        if basename.startswith("_"):
            continue
        algo_candidates.append(basename)
    await send_200(algo_candidates)
