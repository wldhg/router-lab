from threading import Lock as ThreadLock
from typing import Callable, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ExplicitDelDict(Generic[K, V]):
    def __init__(self, name: str):
        self.__name__ = name  # for debug
        self.__items: dict[K, V] = {}
        self.__lock = ThreadLock()

    def __len__(self):
        return len(self.__items)

    def remove(self, key: K):
        with self.__lock:
            if key not in self.__items:
                return
            item = self.__items.pop(key)
            if isinstance(item, list):
                for i in item:
                    del i
            elif isinstance(item, dict):
                for i in item.values():
                    del i
            del item

    def destroy(self):
        keys = list(self.__items.keys())
        for k in keys:
            self.remove(k)

    def get(self, key: K) -> V | None:
        if key not in self.__items:
            return None
        return self.__items[key]

    def add(self, key: K, item: V | Callable[[V | None], V]):
        with self.__lock:
            if callable(item):
                new_item = item(self.__items.get(key, None))
                self.__items[key] = new_item
            else:
                self.__items[key] = item
