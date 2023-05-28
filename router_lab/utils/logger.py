from loguru import logger
from rich.logging import RichHandler


def init_logger(file_name: str):
    logger.remove()
    logger.add(
        f"logs/{file_name}",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra} | {message}",
    )
    logger.add(
        RichHandler(),
        format="{extra} | {message}",
        colorize=False,
        backtrace=True,
        diagnose=True,
        level="DEBUG",
    )
    return logger
