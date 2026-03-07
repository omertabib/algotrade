from src.enums import ActionEnum
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class PriceAlertStrategy(BaseStrategy):
    def __init__(self, symbol: str, threshold: float = 200):
        super().__init__(symbol)
        self.threshold = threshold

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        if tick.symbol != self.symbol: return Result(error="Strategy symbol and tick symbol dosn't match")
        if tick.price > self.threshold:
            signal_result = SignalResult(symbol=self.symbol, strategy=self.__class__.__name__,price=tick.price, action=ActionEnum.BUY, timestamp=tick.timestamp, metadata="Price is over the threshold")
            return Result[SignalResult](value=signal_result)
        return Result(value=SignalResult(
            symbol=tick.symbol,
            price=tick.price,
            strategy=self.__class__.__name__,
            action=ActionEnum.HOLD,
            timestamp=tick.timestamp,
            metadata="Price is under the threshold"
        ))