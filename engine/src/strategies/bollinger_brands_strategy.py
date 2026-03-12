import math
from src.enums import ActionEnum
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy
from src.handlers.redis_handler import RedisHandler

class BollingerBandsStrategy(BaseStrategy):
    def __init__(self, symbol: str, redis_handler: RedisHandler, period: int = 20, std_dev: float = 2.0):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.period = period
        self.std_dev_multiplier = std_dev
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            history = await self.redis_handler.get_prices(self.symbol, self.period)
            if len(history) < self.period:
                return Result(value=self._generate_hold(tick, "Building BB history"))

            # Calculate mean (SMA) and standard deviation
            sma = sum(history) / self.period
            variance = sum((p - sma) ** 2 for p in history) / self.period
            std_dev = math.sqrt(variance)

            # Calculate the bands
            upper_band = sma + (self.std_dev_multiplier * std_dev)
            lower_band = sma - (self.std_dev_multiplier * std_dev)

            current_action = ActionEnum.HOLD
            if tick.price >= upper_band:
                current_action = ActionEnum.SELL
            elif tick.price <= lower_band:
                current_action = ActionEnum.BUY

            if current_action != self.last_signal:
                self.last_signal = current_action
                return Result(value=SignalResult(
                    symbol=self.symbol, price=tick.price, strategy=self.__class__.__name__,
                    action=current_action, timestamp=tick.timestamp,
                    metadata=f"Price touched bands. BB: {lower_band:.2f} - {upper_band:.2f}"
                ))

            return Result(value=self._generate_hold(tick, "Inside bands"))
        except Exception as e:
            return Result(error=f"BB Error: {str(e)}")

    def _generate_hold(self, tick, msg):
        return SignalResult(symbol=self.symbol, price=tick.price, action=ActionEnum.HOLD,
                            strategy=self.__class__.__name__, timestamp=tick.timestamp, metadata=msg)