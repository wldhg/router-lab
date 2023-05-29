from __future__ import annotations

import copy
from threading import Lock, Thread
from typing import Any, Callable, Generic, TypeVar

V = TypeVar("V")


class ThreadedPromiseLike(Generic[V]):
    def __init__(self, data_fn: Callable[[], V]):
        self.__lock = Lock()
        self.__fired_data: V | None = None
        self.__fired_exception: Exception | None = None
        self.__once_list: list[Callable[[V], Any]] = []
        self.__on_list: list[Callable[[V], Any]] = []
        self.__catch_list: list[Callable[[Exception], Any]] = []

        def get_data_and_dispatch():
            try:
                self.__fired_data = data_fn()
            except Exception as e:
                self.__fired_exception = e
                with self.__lock:
                    for callback in self.__catch_list:
                        self.__threaded_exception_firing(callback)
                    self.__on_list.clear()
                    self.__once_list.clear()
            else:
                with self.__lock:
                    for callback in self.__once_list:
                        self.__threaded_data_firing(callback)
                    for callback in self.__on_list:
                        self.__threaded_data_firing(callback)
                    self.__once_list.clear()
                    self.__catch_list.clear()

        Thread(target=get_data_and_dispatch).start()

    def __threaded_data_firing(self, callback: Callable[[V], Any]):
        fired_data = copy.deepcopy(self.__fired_data)
        Thread(target=callback, args=(fired_data,)).start()

    def __threaded_exception_firing(self, callback: Callable[[Exception], Any]):
        Thread(target=callback, args=(self.__fired_exception,)).start()

    def once(self, callback: Callable[[V], Any]) -> ThreadedPromiseLike:
        with self.__lock:
            if self.__fired_data is not None:
                self.__threaded_data_firing(callback)
            elif self.__fired_exception is not None:
                self.__once_list.append(callback)
        return self

    def then(self, callback: Callable[[V], Any]) -> ThreadedPromiseLike:
        with self.__lock:
            if self.__fired_data is not None:
                self.__threaded_data_firing(callback)
            elif self.__fired_exception is not None:
                self.__on_list.append(callback)
        return self

    def catch(self, callback: Callable[[Exception], Any]) -> ThreadedPromiseLike:
        with self.__lock:
            if self.__fired_exception is not None:
                self.__threaded_exception_firing(callback)
            elif self.__fired_data is not None:
                self.__catch_list.append(callback)
        return self
