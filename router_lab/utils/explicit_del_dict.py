from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ExplicitDelDict(Generic[K, V]):
    def __init__(self):
        self.__items: dict[K, V] = {}

    def __len__(self):
        return len(self.__items)

    def remove(self, key: K):
        item = self.__items.pop(key)
        del item

    def get(self, key: K) -> V:
        return self.__items[key]

    def add(self, key: K, item: V):
        if key in self.__items:
            raise KeyError(f"Key {key} already exists.")
        self.__items[key] = item
