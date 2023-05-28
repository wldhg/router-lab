from .__version__ import __version__

SocketResponseSafeType = (
    str | int | float | None | list["SocketResponseSafeType"] | dict[str, "SocketResponseSafeType"]
)


def make_200(data: dict[str, SocketResponseSafeType]) -> dict[str, SocketResponseSafeType]:
    return {"version": str(__version__), "status": 200, **data}


def make_500(e: str) -> dict[str, SocketResponseSafeType]:
    return {"version": str(__version__), "status": 500, "error": e}
