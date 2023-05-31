import asyncio
import logging
from typing import Callable, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ExplicitDelDict(Generic[K, V]):
    def __init__(self, name: str):
        self.__name__ = name  # for debug
        self.__items: dict[K, V] = {}
        self.__lock = asyncio.Lock()

    def __len__(self):
        return len(self.__items)

    async def remove(self, key: K):
        logging.debug(f"EDD = lock {self.__name__} {key} R")
        async with self.__lock:
            if key not in self.__items:
                logging.debug(f"EDD = lock {self.__name__} {key} R not found -> release")
                return
            item = self.__items.pop(key)
            if isinstance(item, list):
                for i in item:
                    del i
            elif isinstance(item, dict):
                for i in item.values():
                    del i
            del item
            logging.debug(f"EDD = lock {self.__name__} {key} R success -> release")

    async def destroy(self):
        keys = list(self.__items.keys())
        for k in keys:
            await self.remove(k)

    def get(self, key: K) -> V | None:
        if key not in self.__items:
            return None
        return self.__items[key]

    async def add(self, key: K, item: V | Callable[[V | None], V]):
        logging.debug(f"EDD = lock {self.__name__} {key} A")
        async with self.__lock:
            if callable(item):
                new_item = item(self.__items.get(key, None))
                self.__items[key] = new_item
            else:
                self.__items[key] = item
            logging.debug(f"EDD = lock {self.__name__} {key} A success -> release")

    def keys(self):
        return self.__items.keys()
