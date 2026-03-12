from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class DonchianChannelStrategy(BaseStrategy):
    def __init__(
        self,
        symbol: str,
        redis_handler: RedisHandler,
        breakout_period: int = 20,
        exit_period: int = 10,
    ):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.breakout_period = breakout_period
        self.exit_period = exit_period
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            history = await self.redis_handler.get_prices(self.symbol, self.breakout_period)
            if len(history) < self.breakout_period:
                return Result(value=self._generate_hold(tick, "Building Donchian history"))

            upper = max(history)
            lower = min(history)

            current_signal = ActionEnum.HOLD
            if tick.price > upper:
                current_signal = ActionEnum.BUY
            elif tick.price < lower:
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
                        metadata=f"Donchian breakout: upper={upper:.2f} lower={lower:.2f}",
                    )
                )

            return Result(value=self._generate_hold(tick, "No breakout"))
        except Exception as e:
            return Result(error=f"DonchianChannel Error: {str(e)}")

    def _generate_hold(self, tick: NormalizedTick, msg: str) -> SignalResult:
        return SignalResult(
            symbol=self.symbol,
            price=tick.price,
            action=ActionEnum.HOLD,
            strategy=self.__class__.__name__,
            timestamp=tick.timestamp,
            metadata=msg,
        )
