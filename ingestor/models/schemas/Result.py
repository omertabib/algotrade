from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import TypeVar, Generic

from models.schemas.Error import Error

T = TypeVar("T")

class Result(BaseModel, Generic[T]):
    value: Optional[T] = Field(default=None, description="The result object")
    error: Optional[Error] = Field(default=None, description="Error in case of an error")