import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.clients.redis_client import RedisClient
from src.execution_engine import ExecutionEngine
from src.handlers.redis_handler import RedisHandler
from src.mock_portfolio import MockPortfolio
from src.signals_engine import SignalEngine
from src.strategies.bollinger_brands_strategy import BollingerBandsStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.price_alert_strategy import PriceAlertStrategy
from src.strategies.sma_crossover_strategy import SMACrossoverStrategy
from src.strategies.vwap_strategy import VWAPStrategy
from src.strategies.zscore_strategy import ZScoreStrategy


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    redis_broker = RedisClient()
    execution_engine = ExecutionEngine(MockPortfolio())
    await redis_broker.connect()

    redis_handler = RedisHandler(await redis_broker.get_connection())

    signal_engine = SignalEngine(subscriber=redis_broker, cache_handler=redis_handler, execution=execution_engine)

    # 2. Configuration Map: Define custom parameters for each symbol
    STRATEGY_CONFIG = {
        "AAPL": {"threshold": 230, "fast": 5, "slow": 20},
        "TSLA": {"threshold": 350, "fast": 10, "slow": 30},
        "GOOG": {"threshold": 170, "fast": 5, "slow": 20},
        "BTC/USD": {"threshold": 95000, "fast": 20, "slow": 100}  # Crypto needs longer windows
    }

    # 3. Dynamic Registration with custom parameters
    for symbol, config in STRATEGY_CONFIG.items():
        print(f"🛠️ Registering tailored strategies for {symbol}...")

        # Price Alert with custom threshold
        await signal_engine.subscribe_to_symbol(
            symbol=symbol,
            strategy=PriceAlertStrategy(symbol=symbol, threshold=config["threshold"])
        )

        # SMA Crossover with custom periods
        await signal_engine.subscribe_to_symbol(
            symbol=symbol,
            strategy=SMACrossoverStrategy(
                symbol=symbol,
                redis_handler=redis_handler,
                fast_period=config["fast"],
                slow_period=config["slow"]
            )
        )

        # Bollinger Bands & VWAP (can also be customized in the same way)
        await signal_engine.subscribe_to_symbol(symbol=symbol, strategy=BollingerBandsStrategy(symbol, redis_handler))
        await signal_engine.subscribe_to_symbol(symbol=symbol, strategy=VWAPStrategy(symbol, redis_handler))
        # Adding MACD
        await signal_engine.subscribe_to_symbol(
            symbol=symbol,
            strategy=MACDStrategy(symbol=symbol, redis_handler=redis_handler)
        )

        # Adding Z-Score
        await signal_engine.subscribe_to_symbol(
            symbol=symbol,
            strategy=ZScoreStrategy(symbol=symbol, redis_handler=redis_handler, period=config.get("slow", 30))
        )
        await signal_engine.subscribe_to_symbol(symbol=symbol, strategy=VWAPStrategy(symbol, redis_handler))
    task = asyncio.create_task(signal_engine.listen_and_process())
    yield

    # Shutdown:
    task.cancel()
    await redis_broker.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "provider": "Alpaca"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)