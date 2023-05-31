from __future__ import annotations

import asyncio
import copy
import logging
from typing import Any, Awaitable, Callable, Generic, TypeVar

from .undefined import UNDEFINED, UndefinedType

V = TypeVar("V")


class PromiseLike(Generic[V]):
    def __init__(self, data_fn: Callable[[], V] | Awaitable[V]):
        self.__lock = asyncio.Lock()
        self.__fired_data: V | UndefinedType = UNDEFINED
        self.__fired_exception: Exception | UndefinedType = UNDEFINED
        self.__once_list: list[Callable[[V], Any]] = []
        self.__on_list: list[Callable[[V], Any]] = []
        self.__catch_list: list[Callable[[Exception], Any]] = []

        async def get_data_and_dispatch():
            try:
                if asyncio.iscoroutine(data_fn):
                    self.__fired_data = await data_fn
                elif callable(data_fn):
                    self.__fired_data = data_fn()
                else:
                    raise TypeError("data_fn must be callable or awaitable: " + str(data_fn))
            except Exception as e:
                self.__fired_exception = e
                logging.debug("PRM = lock 1 entered")
                async with self.__lock:
                    for callback in self.__catch_list:
                        await self.__exception_firing(callback)
                    self.__on_list.clear()
                    self.__once_list.clear()
                    logging.debug("PRM = lock 1 exited")
            else:
                logging.debug("PRM = lock 2 entered")
                async with self.__lock:
                    for callback in self.__once_list:
                        await self.__data_firing(callback)
                    for callback in self.__on_list:
                        await self.__data_firing(callback)
                    self.__once_list.clear()
                    self.__catch_list.clear()
                    logging.debug("PRM = lock 2 exited")

        asyncio.create_task(get_data_and_dispatch())

    async def __data_firing(self, callback: Callable[[V], Any]):
        if self.__fired_data == UNDEFINED:
            return
        fired_data = copy.deepcopy(self.__fired_data)
        retval = callback(fired_data)
        if asyncio.iscoroutine(retval):
            await retval

    async def __exception_firing(self, callback: Callable[[Exception], Any]):
        if self.__fired_exception == UNDEFINED:
            return
        retval = callback(self.__fired_exception)
        if asyncio.iscoroutine(retval):
            await retval

    def once(self, callback: Callable[[V], Any]) -> PromiseLike:
        async def _once():
            logging.debug("PRM = lock 3 entered")
            async with self.__lock:
                if self.__fired_data != UNDEFINED:
                    logging.debug("PRM = lock 3 fire 1")
                    asyncio.create_task(self.__data_firing(callback))
                elif self.__fired_exception == UNDEFINED:
                    logging.debug("PRM = lock 3 fire 2")
                    self.__once_list.append(callback)
                logging.debug("PRM = lock 3 exited")

        asyncio.create_task(_once())
        return self

    def then(self, callback: Callable[[V], Any]) -> PromiseLike:
        async def _then():
            logging.debug("PRM = lock 4 entered")
            async with self.__lock:
                if self.__fired_data != UNDEFINED:
                    asyncio.create_task(self.__data_firing(callback))
                elif self.__fired_exception == UNDEFINED:
                    self.__on_list.append(callback)
                logging.debug("PRM = lock 4 exited")

        asyncio.create_task(_then())
        return self

    def catch(self, callback: Callable[[Exception], Any]) -> PromiseLike:
        async def _catch():
            logging.debug("PRM = lock 5 entered")
            async with self.__lock:
                if self.__fired_exception != UNDEFINED:
                    asyncio.create_task(self.__exception_firing(callback))
                elif self.__fired_data == UNDEFINED:
                    self.__catch_list.append(callback)
                logging.debug("PRM = lock 5 exited")

        asyncio.create_task(_catch())
        return self
