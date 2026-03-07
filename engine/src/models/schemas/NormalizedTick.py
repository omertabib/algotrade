from pydantic import BaseModel, Field


class NormalizedTick(BaseModel):
    symbol: str = Field(description="Symbol")
    price: float = Field(description="Price")
    quantity: int = Field(description="Quantity")
    timestamp: int = Field(description="Unix Timestamp")
    received_at: int = Field(description="When was the request received in our server")

