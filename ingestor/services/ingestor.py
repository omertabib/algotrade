from alpaca.data.live import StockDataStream
from data_providers.AlpacaDataProvider import AlpacaDataProvider
from models.dto.AlpacaTick import AlpacaTick

from handlers.redis_handler import RedisIngestHandler


class DataIngestor:
    """
    Service responsible for streaming real-time data from Alpaca
    and ingesting it into the system via Redis.
    """

    def __init__(self, api_key: str, secret_key: str, redis_connection):
        self.api_key = api_key
        self.secret_key = secret_key
        # The handler now receives the actual aioredis object
        self.redis_handler = RedisIngestHandler(redis_connection)

        self.stream = StockDataStream(self.api_key, self.secret_key)
        self.symbols = []

    async def _on_trade(self, data):
        try:
            # Pydantic will now map the SDK Trade object attributes to AlpacaTick fields
            dto = AlpacaTick.model_validate(data)

            result = AlpacaDataProvider.transform_data(dto)

            if result.value:
                await self.redis_handler.publish_and_cache(result.value)
                print(f"📡 {result.value.symbol} | Price: {result.value.price} | Vol: {result.value.quantity}")
                # 3. Publish to Redis and update the cache for the Signal Engines
                await self.redis_handler.publish_and_cache(result.value)
            elif result.error:
                print(f"Data Validation Warning: {result.error.message}")

        except Exception as e:
            print(f"Failed to process trade message: {e}")

    async def start_streaming(self, symbols: list[str]):
        # Filter only stocks for the StockDataStream to avoid 400 errors
        stock_symbols = [s for s in symbols if "/" not in s]
        print(f"🚀 Starting live ingestion for Stocks: {stock_symbols}")

        try:
            self.stream.subscribe_trades(self._on_trade, *stock_symbols)
            await self.stream._run_forever()
        except Exception as e:
            print(f"❌ Alpaca Stream Error: {e}")

    async def stop(self):
        """
        Gracefully shuts down the stream and cleans up resources.
        """
        print("Stopping Data Ingestor...")
        await self.stream.stop()