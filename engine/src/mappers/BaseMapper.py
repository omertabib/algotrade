import abc
from typing import TypeVar, Generic

T = TypeVar('T')


class BaseMapper(abc.ABC, Generic[T]):
    @staticmethod
    @abc.abstractmethod
    def map(message: dict) -> T:
        pass
