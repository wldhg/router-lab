from abc import ABC, abstractmethod


class ExperimentBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def metrics(self):
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
