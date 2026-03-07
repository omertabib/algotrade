from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    def __init__(self, symbol: str, redis_handler: RedisHandler, period: int = 14):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.period = period

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            # We need one extra price to calculate the first change
            history = await self.redis_handler.get_prices(self.symbol, self.period + 1)
            if len(history) < self.period + 1:
                return Result(value=self._generate_hold(tick, "Building RSI history"))

            gains = []
            losses = []
            # Calculate changes between consecutive prices
            for i in range(len(history) - 1):
                change = history[i] - history[i+1] # Newest is index 0
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / self.period
            avg_loss = sum(losses) / self.period

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            action = ActionEnum.HOLD
            if rsi < 30: action = ActionEnum.BUY
            elif rsi > 70: action = ActionEnum.SELL

            return Result(value=SignalResult(
                symbol=self.symbol, price=tick.price, strategy=self.__class__.__name__,
                action=action, timestamp=tick.timestamp, metadata=f"RSI: {rsi:.2f}"
            ))
        except Exception as e:
            return Result(error=f"RSI Error: {e}")