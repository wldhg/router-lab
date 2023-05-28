from abc import ABC
from typing import Callable


class EventDispatcher(ABC):
    def __init__(self):
        self.__once_dict: dict[str, list[Callable]] = {}
        self.__on_dict: dict[str, list[Callable]] = {}

    def _dispatch(self, event: str, *args, **kwargs):  # pyright: ignore[reportMissingParameterType]
        if event in self.__once_dict:
            for callback in self.__once_dict[event]:
                callback(*args, **kwargs)
            del self.__once_dict[event]
        if event in self.__on_dict:
            for callback in self.__on_dict[event]:
                callback(*args, **kwargs)

    def once(self, event: str, callback: Callable):
        if event not in self.__once_dict:
            self.__once_dict[event] = []
        self.__once_dict[event].append(callback)

    def on(self, event: str, callback: Callable):
        if event not in self.__on_dict:
            self.__on_dict[event] = []
        self.__on_dict[event].append(callback)

    def off(self, event: str, callback: Callable):
        if event in self.__once_dict:
            self.__once_dict[event].remove(callback)
        if event in self.__on_dict:
            self.__on_dict[event].remove(callback)
