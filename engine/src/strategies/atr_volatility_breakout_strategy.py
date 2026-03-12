from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class ATRVolatilityBreakoutStrategy(BaseStrategy):
    def __init__(
        self,
        symbol: str,
        redis_handler: RedisHandler,
        lookback_period: int = 20,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
    ):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.lookback_period = lookback_period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            needed = max(self.lookback_period, self.atr_period)
            history = await self.redis_handler.get_prices(self.symbol, needed)
            if len(history) < needed:
                return Result(value=self._generate_hold(tick, "Building ATR breakout history"))

            range_high = max(history[: self.lookback_period])
            range_low = min(history[: self.lookback_period])

            deltas = [
                abs(history[i] - history[i + 1])
                for i in range(self.atr_period - 1)
            ]
            atr_proxy = sum(deltas) / len(deltas) if deltas else 0.0

            buy_level = range_high + self.atr_multiplier * atr_proxy
            sell_level = range_low - self.atr_multiplier * atr_proxy

            current_signal = ActionEnum.HOLD
            if tick.price > buy_level:
                current_signal = ActionEnum.BUY
            elif tick.price < sell_level:
                current_signal = ActionEnum.SELL

            if current_signal != self.last_signal:
                self.last_signal = current_signal
                return Result(
                    value=SignalResult(
                        symbol=self.symbol,
                        price=tick.price,
                        strategy=self.__class__.__name__,
                        action=current_signal,
                        timestamp=tick.timestamp,
                        metadata=f"ATR breakout: range=[{range_low:.2f},{range_high:.2f}] atr={atr_proxy:.2f}",
                    )
                )

            return Result(value=self._generate_hold(tick, "No ATR breakout"))
        except Exception as e:
            return Result(error=f"ATRVolatilityBreakout Error: {str(e)}")

    def _generate_hold(self, tick: NormalizedTick, msg: str) -> SignalResult:
        return SignalResult(
            symbol=self.symbol,
            price=tick.price,
            action=ActionEnum.HOLD,
            strategy=self.__class__.__name__,
            timestamp=tick.timestamp,
            metadata=msg,
        )
