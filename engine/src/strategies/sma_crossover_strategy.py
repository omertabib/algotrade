from src.enums import ActionEnum
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy
from src.handlers.redis_handler import RedisHandler

class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, symbol: str, redis_handler: RedisHandler, fast_period: int = 5, slow_period: int = 20):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            # 1. Fetch price history from Redis (need enough prices for the slow average)
            history = await self.redis_handler.get_prices(self.symbol, self.slow_period)

            # 2. Verify enough data in cache
            if len(history) < self.slow_period:
                return Result(value=self._generate_hold(tick, "Insufficient history in Redis"))

            # 3. Calculate the averages
            # Redis returns list newest-to-oldest (due to LPUSH), so history[:fast] is the most recent
            fast_sma = sum(history[:self.fast_period]) / self.fast_period
            slow_sma = sum(history) / self.slow_period

            # 4. Crossover logic
            current_signal = ActionEnum.HOLD
            if fast_sma > slow_sma:
                current_signal = ActionEnum.BUY
            elif fast_sma < slow_sma:
                current_signal = ActionEnum.SELL

            # 5. Only emit a signal on state change
            if current_signal != self.last_signal:
                self.last_signal = current_signal
                return Result(value=SignalResult(
                    symbol=self.symbol,
                    price=tick.price,
                    strategy=self.__class__.__name__,
                    action=current_signal,
                    timestamp=tick.timestamp,
                    metadata=f"SMA Cross: Fast({fast_sma:.2f}) {'↑' if current_signal == ActionEnum.BUY else '↓'} Slow({slow_sma:.2f})"
                ))

            return Result(value=self._generate_hold(tick, "No crossover change"))

        except Exception as e:
            return Result(error=f"Strategy Error: {str(e)}")

    def _generate_hold(self, tick, msg):
        return SignalResult(
            symbol=self.symbol,
            price=tick.price,
            action=ActionEnum.HOLD,
            strategy=self.__class__.__name__,
            timestamp=tick.timestamp,
            metadata=msg
        )