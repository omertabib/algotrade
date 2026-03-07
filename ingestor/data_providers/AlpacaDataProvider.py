from datetime import datetime
from typing import TypeVar

from .DataProvider import DataProvider
from models.dto.AlpacaTick import AlpacaTick
from models.schemas.NormalizedTick import NormalizedTick
from models.schemas.Result import Result
from models.schemas.Error import Error

T = TypeVar("T")


class AlpacaDataProvider(DataProvider[AlpacaTick]):

    @classmethod
    def transform_data(cls, dto_object: AlpacaTick) -> Result:
        if dto_object.p <= 0:
            return Result(error=Error(code=100, message="Price must be greater than 0"))

        # The SDK already provides 't' as a datetime object
        normalized_data = {
            "symbol": dto_object.S,
            "price": dto_object.p,
            "quantity": dto_object.s,
            "timestamp": int(dto_object.t.timestamp() * 1000),
            "received_at": int(datetime.now().timestamp() * 1000)
        }

        return Result[NormalizedTick](value=NormalizedTick.model_validate(normalized_data))