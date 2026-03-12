from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class TSMomentumStrategy(BaseStrategy):
    def __init__(
        self,
        symbol: str,
        redis_handler: RedisHandler,
        momentum_lookback: int = 20,
        threshold_return: float = 0.02,
    ):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.momentum_lookback = momentum_lookback
        self.threshold_return = threshold_return
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            history = await self.redis_handler.get_prices(self.symbol, self.momentum_lookback)
            if len(history) < self.momentum_lookback:
                return Result(value=self._generate_hold(tick, "Building TS Momentum history"))

            price_now = tick.price
            price_old = history[self.momentum_lookback - 1]
            if price_old <= 0:
                return Result(value=self._generate_hold(tick, "Invalid price_old"))
            r = (price_now / price_old) - 1

            current_signal = ActionEnum.HOLD
            if r >= self.threshold_return:
                current_signal = ActionEnum.BUY
            elif r <= -self.threshold_return:
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
                        metadata=f"TS Momentum R={r:.4f} (threshold=±{self.threshold_return})",
                    )
                )

            return Result(value=self._generate_hold(tick, "Within threshold"))
        except Exception as e:
            return Result(error=f"TSMomentum Error: {str(e)}")

    def _generate_hold(self, tick: NormalizedTick, msg: str) -> SignalResult:
        return SignalResult(
            symbol=self.symbol,
            price=tick.price,
            action=ActionEnum.HOLD,
            strategy=self.__class__.__name__,
            timestamp=tick.timestamp,
            metadata=msg,
        )
