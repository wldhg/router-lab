import loguru
from loguru import logger
from rich.logging import RichHandler


def log_formatter(ctx_fmt_str: str):
    def _log_formatter(record: "loguru.Record") -> str:
        ctx_string = " ".join(
            [f"{k}={repr(v)}" for k, v in record["extra"].items() if k not in ["__ctx__", "ctx"]]
        )

        if "ctx" in record["extra"]:
            ctx_string = (" " if len(ctx_string) > 0 else "").join(
                ["<" + record["extra"]["ctx"] + ">", ctx_string]
            )

        if len(ctx_string) > 0:
            ctx_string += " | "

        record["extra"]["__ctx__"] = ctx_string
        return ctx_fmt_str

    return _log_formatter


def init_logger(file_name: str):
    logger.remove()
    logger.add(
        f"logs/{file_name}",
        format=log_formatter(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra[__ctx__]}{message}\n"
        ),
    )
    logger.add(
        RichHandler(),
        format=log_formatter("{extra[__ctx__]}{message}"),
        colorize=False,
        backtrace=True,
        diagnose=True,
        level="DEBUG",
    )
    return logger
