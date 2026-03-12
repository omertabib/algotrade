from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class PullbackToMAStrategy(BaseStrategy):
    def __init__(
        self,
        symbol: str,
        redis_handler: RedisHandler,
        short_period: int = 5,
        long_period: int = 20,
        dip_pct: float = 0.01,
        rally_pct: float = 0.01,
    ):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.short_period = short_period
        self.long_period = long_period
        self.dip_pct = dip_pct
        self.rally_pct = rally_pct
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            history = await self.redis_handler.get_prices(self.symbol, self.long_period)
            if len(history) < self.long_period:
                return Result(value=self._generate_hold(tick, "Building Pullback-to-MA history"))

            short_ma = sum(history[: self.short_period]) / self.short_period
            long_ma = sum(history[: self.long_period]) / self.long_period

            uptrend = short_ma > long_ma
            downtrend = short_ma < long_ma

            current_signal = ActionEnum.HOLD
            if uptrend:
                if tick.price < short_ma * (1 - self.dip_pct) and tick.price > long_ma:
                    current_signal = ActionEnum.BUY
            elif downtrend:
                if tick.price > short_ma * (1 + self.rally_pct) and tick.price < long_ma:
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
                        metadata=f"Pullback: short_ma={short_ma:.2f} long_ma={long_ma:.2f}",
                    )
                )

            return Result(value=self._generate_hold(tick, "No pullback signal"))
        except Exception as e:
            return Result(error=f"PullbackToMA Error: {str(e)}")

    def _generate_hold(self, tick: NormalizedTick, msg: str) -> SignalResult:
        return SignalResult(
            symbol=self.symbol,
            price=tick.price,
            action=ActionEnum.HOLD,
            strategy=self.__class__.__name__,
            timestamp=tick.timestamp,
            metadata=msg,
        )
