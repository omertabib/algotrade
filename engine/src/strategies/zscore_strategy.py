import math

from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class ZScoreStrategy(BaseStrategy):
    def __init__(self, symbol: str, redis_handler: RedisHandler, period: int = 30, entry_threshold: float = 2.0):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.period = period
        self.threshold = entry_threshold # Standard deviation units

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            history = await self.redis_handler.get_prices(self.symbol, self.period)
            if len(history) < self.period:
                return Result(value=self._generate_hold(tick, "Building Z-Score history"))

            # Calculate Mean and Standard Deviation
            mean = sum(history) / self.period
            variance = sum((p - mean) ** 2 for p in history) / self.period
            std_dev = math.sqrt(variance)

            if std_dev == 0:
                return Result(value=self._generate_hold(tick, "Zero volatility"))

            # Calculate Z-Score: How many std devs is the current price from the mean?
            z_score = (tick.price - mean) / std_dev

            action = ActionEnum.HOLD
            # If price is more than 2 std devs BELOW mean -> Undervalued
            if z_score < -self.threshold:
                action = ActionEnum.BUY
            # If price is more than 2 std devs ABOVE mean -> Overvalued
            elif z_score > self.threshold:
                action = ActionEnum.SELL

            return Result(value=SignalResult(
                symbol=self.symbol, price=tick.price, strategy=self.__class__.__name__,
                action=action, timestamp=tick.timestamp,
                metadata=f"Z-Score: {z_score:.2f} (StdDev: {std_dev:.2f})"
            ))
        except Exception as e:
            return Result(error=f"Z-Score Error: {e}")

    def _generate_hold(self, tick: NormalizedTick, param: str) -> SignalResult:
        return SignalResult(
            symbol=self.symbol,
            price=tick.price,
            action=ActionEnum.HOLD,
            strategy=self.__class__.__name__,
            timestamp=tick.timestamp,
            metadata=param,
        )