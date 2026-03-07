from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseSubscriber(ABC):
    @abstractmethod
    async def subscribe(self, *args, **kwargs) -> AsyncIterator[dict]:
        pass