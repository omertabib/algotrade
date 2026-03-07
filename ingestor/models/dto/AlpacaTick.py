from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List


class AlpacaTick(BaseModel):
    # Allow mapping from object attributes (SDK Trade object)
    model_config = ConfigDict(from_attributes=True)

    # Use aliases to match the SDK Trade object fields
    S: str = Field(alias="symbol", description="Symbol")
    p: float = Field(alias="price", description="Price")
    s: int = Field(alias="size", description="Quantity/Size")
    t: datetime = Field(alias="timestamp", description="Timestamp object")

    # Optional fields if you need them later
    x: str = Field(alias="exchange", default="", description="Exchange")
    i: int = Field(alias="id", default=0, description="Trade ID")