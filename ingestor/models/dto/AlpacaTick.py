from pydantic import BaseModel, Field


class AlpacaTick(BaseModel):
    T: str = Field(description="Message Type")
    S: str = Field(description="Symbol")
    i: int = Field(description="Trade ID")
    x: str = Field(description="Exchange")
    p: float = Field(description="Price")
    s: int = Field(description="Size")
    t: str = Field(description="Timestamp")
    c: list[str] = Field(description="Conditions")
