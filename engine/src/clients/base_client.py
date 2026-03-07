from abc import ABCMeta, abstractmethod, ABC


class BaseClient(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        pass
