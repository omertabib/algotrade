from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class VWAPStrategy(BaseStrategy):
    def __init__(self, symbol: str, redis_handler: RedisHandler, period: int = 50):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.period = period
        self.last_signal = ActionEnum.HOLD

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            # Step A: Save the tick with its volume to Redis
            await self.redis_handler.save_tick_with_volume(tick.symbol, tick.price, tick.quantity, self.period)

            # Step B: Fetch combined history (price:volume)
            key = f"history_v:{self.symbol}"
            raw_data = await self.redis_handler._db.lrange(key, 0, self.period - 1)

            if len(raw_data) < self.period:
                return Result(value=self._generate_hold(tick, "Building VWAP history"))

            total_pv = 0.0  # Price * Volume
            total_volume = 0

            for entry in raw_data:
                p, v = map(float, entry.split(":"))
                total_pv += (p * v)
                total_volume += v

            vwap = total_pv / total_volume

            # Logic: price above VWAP is bullish (buy), below is bearish (sell)
            current_action = ActionEnum.BUY if tick.price > vwap else ActionEnum.SELL

            if current_action != self.last_signal:
                self.last_signal = current_action
                return Result(value=SignalResult(
                    symbol=self.symbol, price=tick.price, strategy=self.__class__.__name__,
                    action=current_action, timestamp=tick.timestamp,
                    metadata=f"VWAP Cross: {vwap:.2f}"
                ))

            return Result(value=self._generate_hold(tick, f"Price relative to VWAP: {vwap:.2f}"))
        except Exception as e:
            return Result(error=f"VWAP Error: {str(e)}")

    def _generate_hold(self, tick, msg):
        return SignalResult(symbol=self.symbol, price=tick.price, action=ActionEnum.HOLD,
                            strategy=self.__class__.__name__, timestamp=tick.timestamp, metadata=msg)