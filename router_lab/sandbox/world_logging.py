import logging

import loguru


class WorldLoggingHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.buffer: list[loguru.Record] = []

    def emit(self, record: loguru.Record):
        self.buffer.append(record)

    def flush(self) -> list[loguru.Record]:
        self.acquire()
        buffer_copy = self.buffer.copy()
        try:
            self.buffer.clear()
        finally:
            self.release()
        return buffer_copy

    def close(self):
        logging.Handler.close(self)
