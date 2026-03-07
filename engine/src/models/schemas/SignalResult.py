from typing import Optional

from pydantic import BaseModel

from src.enums import ActionEnum


class SignalResult(BaseModel):
    symbol: str
    strategy: Optional[str] = None
    price: float
    action: ActionEnum
    timestamp: int
    metadata: str
