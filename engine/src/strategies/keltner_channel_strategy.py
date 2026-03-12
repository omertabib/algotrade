from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class KeltnerChannelStrategy(BaseStrategy):
    def __init__(
        self,
        symbol: str,
        redis_handler: RedisHandler,
        ema_period: int = 20,
        atr_period: int = 14,
        multiplier: float = 2.0,
    ):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            needed = max(self.ema_period, self.atr_period) + 1
            history = await self.redis_handler.get_prices(self.symbol, needed)
            if len(history) < needed:
                return Result(value=self._generate_hold(tick, "Building Keltner history"))

            ema = sum(history[: self.ema_period]) / self.ema_period

            deltas = [
                abs(history[i] - history[i + 1])
                for i in range(self.atr_period - 1)
            ]
            atr_proxy = sum(deltas) / len(deltas) if deltas else 0.0

            upper = ema + self.multiplier * atr_proxy
            lower = ema - self.multiplier * atr_proxy

            current_signal = ActionEnum.HOLD
            if tick.price <= lower:
                current_signal = ActionEnum.BUY
            elif tick.price >= upper:
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
                        metadata=f"Keltner: ema={ema:.2f} upper={upper:.2f} lower={lower:.2f}",
                    )
                )

            return Result(value=self._generate_hold(tick, "Inside Keltner channel"))
        except Exception as e:
            return Result(error=f"KeltnerChannel Error: {str(e)}")

    def _generate_hold(self, tick: NormalizedTick, msg: str) -> SignalResult:
        return SignalResult(
            symbol=self.symbol,
            price=tick.price,
            action=ActionEnum.HOLD,
            strategy=self.__class__.__name__,
            timestamp=tick.timestamp,
            metadata=msg,
        )
