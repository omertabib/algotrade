import abc
from abc import abstractmethod
from typing_extensions import TypeVar, Generic
from models.schemas import Result

T = TypeVar("T")

class DataProvider(abc.ABC, Generic[T]):

    @classmethod
    @abstractmethod
    def transform_data(cls, dto_object: T) -> Result:
        pass