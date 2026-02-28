from datetime import datetime
from typing import Union

from dateutil import parser
from typing_extensions import TypeVar
from data_providers.DataProvider import DataProvider
from models.dto.AlpacaTick import AlpacaTick
from models.schemas.Error import Error
from models.schemas.NormalizedTick import NormalizedTick
from models.schemas.Result import Result

T = TypeVar("T")

class AlpacaDataProvider(DataProvider[AlpacaTick]):

    @classmethod
    def transform_data(cls, dto_object: AlpacaTick) -> Result:
        normalized_data = {}
        if dto_object.p == 0:
            return Result(error=Error(code=100, message="Price cannot be 0"))
        normalized_data["timestamp"] = int(parser.parse(dto_object.t).timestamp() * 1000)
        normalized_data["received_at"] = int(datetime.now().timestamp() * 1000)
        normalized_data["symbol"] = dto_object.S
        normalized_data["price"] = dto_object.p
        normalized_data["quantity"] = dto_object.s

        return Result[NormalizedTick](value=NormalizedTick.model_validate(normalized_data))


