from abc import ABC, abstractmethod

from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult


class BaseStrategy(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol

    @abstractmethod
    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        pass