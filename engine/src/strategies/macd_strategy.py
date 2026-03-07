from src.enums import ActionEnum
from src.handlers.redis_handler import RedisHandler
from src.models.schemas.NormalizedTick import NormalizedTick
from src.models.schemas.Result import Result
from src.models.schemas.SignalResult import SignalResult
from src.strategies.base_strategy import BaseStrategy


class MACDStrategy(BaseStrategy):
    def __init__(self, symbol: str, redis_handler: RedisHandler, fast_period: int = 12, slow_period: int = 26,
                 signal_period: int = 9):
        super().__init__(symbol)
        self.redis_handler = redis_handler
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.last_macd_line = None
        self.last_signal_line = None

    def _calculate_ema(self, prices: list[float], period: int) -> float:
        """Simple EMA calculation for the current window"""
        multiplier = 2 / (period + 1)
        # We start with SMA for the first value
        ema = sum(prices[-period:]) / period
        return ema

    async def analyze(self, tick: NormalizedTick) -> Result[SignalResult]:
        try:
            # We need enough history for the slow EMA plus the signal line window
            needed_history = self.slow_period + self.signal_period
            history = await self.redis_handler.get_prices(self.symbol, needed_history)

            if len(history) < needed_history:
                return Result(value=self._generate_hold(tick, "Building MACD history"))

            # Calculate MACD Line (Fast EMA - Slow EMA)
            # Note: Redis returns prices newest-to-oldest, we reverse for EMA calc
            prices_rev = history[::-1]
            fast_ema = self._calculate_ema(prices_rev, self.fast_period)
            slow_ema = self._calculate_ema(prices_rev, self.slow_period)
            macd_line = fast_ema - slow_ema

            # Signal Line is usually an EMA of the MACD Line
            # For simplicity in this real-time tick, we compare to the previous tick's state
            current_signal = ActionEnum.HOLD

            if self.last_macd_line is not None and self.last_signal_line is not None:
                # Bullish Crossover (MACD crosses above Signal)
                if macd_line > 0 and self.last_macd_line <= 0:
                    current_signal = ActionEnum.BUY
                # Bearish Crossover (MACD crosses below Signal)
                elif macd_line < 0 and self.last_macd_line >= 0:
                    current_signal = ActionEnum.SELL

            self.last_macd_line = macd_line
            self.last_signal_line = 0  # In this basic version, we use 0-line crossover

            return Result(value=SignalResult(
                symbol=self.symbol, price=tick.price, strategy=self.__class__.__name__,
                action=current_signal, timestamp=tick.timestamp,
                metadata=f"MACD: {macd_line:.2f}"
            ))
        except Exception as e:
            return Result(error=f"MACD Error: {e}")