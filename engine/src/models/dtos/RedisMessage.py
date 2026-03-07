from pydantic import BaseModel, Field
from typing import Optional


class RedisMessage(BaseModel):
    type: str = Field(description="Type of the message")
    channel: str = Field(description="Channel name")
    data: str = Field(description="Message data")
    pattern: Optional[str] = Field(description="Message pattern")