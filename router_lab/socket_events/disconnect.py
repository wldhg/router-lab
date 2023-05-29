from typing import Any, Callable

import loguru

from ..parts import RouterLabParts


async def disconnect(
    rlp: RouterLabParts,
    log: "loguru.Logger",
    send_200: Callable[[dict], Any],
    send_500: Callable[[str], Any],
    get_data: Callable[[str], Any],
    sid: str,
):
    rlp.sandboxes.remove(sid)

    sub_thrs_stopper = rlp.subscribe_thrs_stop_event.get(sid)
    if sub_thrs_stopper is not None:
        sub_thrs_stopper.set()
    sub_thrs = rlp.subscribe_thrs.get(sid)
    if sub_thrs is not None:
        for thr in sub_thrs:
            thr.join()
    rlp.subscribe_thrs.remove(sid)
    rlp.subscribe_thrs_stop_event.remove(sid)
