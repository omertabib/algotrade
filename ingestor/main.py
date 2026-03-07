import asyncio
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

from clients.redis_client import RedisClient
from handlers.redis_handler import RedisIngestHandler
from services.ingestor import DataIngestor

# Configuration - Best practice: Use environment variables
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "YOUR_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "YOUR_SECRET_KEY")
SYMBOLS_TO_TRACK = ["AAPL", "TSLA", "GOOG", "BTC/USD"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Redis Connection
    redis_client = RedisClient()
    await redis_client.connect()

    # 2. Extract the actual Redis connection object
    # Use the helper method we added to get the raw aioredis connection
    raw_connection = await redis_client.get_connection()

    # 3. Initialize the Ingestor Service with the raw connection
    ingestor = DataIngestor(
        api_key=ALPACA_API_KEY,
        secret_key=ALPACA_SECRET_KEY,
        redis_connection=raw_connection  # Pass raw connection here
    )

    # 3. Start the Alpaca Stream as a Background Task
    # This prevents the FastAPI server from blocking
    ingestion_task = asyncio.create_task(ingestor.start_streaming(SYMBOLS_TO_TRACK))

    # Store references in app state for access if needed
    app.state.ingestor = ingestor
    app.state.redis = redis_client

    print(f"✅ Ingestor Micro-service is running. Tracking: {SYMBOLS_TO_TRACK}")

    yield

    # 4. Graceful Shutdown
    print("Shutting down Ingestor Micro-service...")
    ingestion_task.cancel()
    try:
        await ingestor.stop()
        await redis_client.disconnect()
    except Exception as e:
        print(f"Error during shutdown: {e}")


# Initialize FastAPI app with the lifespan manager
app = FastAPI(
    title="Trading System Ingestor",
    description="Micro-service for real-time market data ingestion",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """
    Monitor the health of the ingestor and its connections.

    """
    redis_status = await app.state.redis.is_healthy()
    return {
        "status": "healthy",
        "redis_connected": redis_status,
        "tracked_symbols": SYMBOLS_TO_TRACK,
        "provider": "Alpaca"
    }


if __name__ == "__main__":
    import uvicorn

    # Run the server on port 8000 (standard for your ingestor setup)
    uvicorn.run(app, host="0.0.0.0", port=8000)