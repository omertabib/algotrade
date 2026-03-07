from optparse import Option
from typing import Any, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypeVar, Generic

from src.models.schemas.Error import Error

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    value: Optional[T] = Field(default=None, description="The result object")
    error: Optional[str] = Field(default=None, description="Error in case of an error")

    @property
    def is_success(self) -> bool:
        return self.error is None
