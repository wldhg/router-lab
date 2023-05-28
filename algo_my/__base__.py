import os
from abc import ABC, abstractmethod


class RLabAlgoBase(ABC):
    @abstractmethod
    async def routing(self, *args, **kwargs):
        pass

    @abstractmethod
    async def general(self, *args, **kwargs):
        pass
