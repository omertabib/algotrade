from typing import TypeVar, Generic
from pydantic import BaseModel, ValidationError

from src.mappers.BaseMapper import BaseMapper
from src.models.schemas.Error import Error
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result

T = TypeVar('T', bound=BaseModel)


class RedisSignalMapper(BaseMapper, Generic[T]):
    @staticmethod
    def map(message: dict) -> Result:
        try:
            return Result[NormalizedTick](value=NormalizedTick.model_validate_json(message['data']))
        except ValidationError:
            return Result(error="Validation error in Redis message")
        except Exception:
            return Result(error=f"General error in Redis message {message}")
