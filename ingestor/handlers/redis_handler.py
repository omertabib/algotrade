import redis.asyncio as aioredis
from models.schemas.NormalizedTick import NormalizedTick


class RedisIngestHandler:
    """
    Handles Redis operations for the Ingestor service,
    including data distribution and historical caching.
    """

    def __init__(self, connection: aioredis.Redis):
        """
        Initialize the handler with an active Redis connection.
        :param connection: An instance of aioredis.Redis
        """
        self._db = connection

    async def publish_and_cache(self, tick: NormalizedTick, max_history: int = 100):
        """
        Publishes the normalized tick to a Redis channel and
        updates the historical price list in a single atomic transaction.

        :param tick: The NormalizedTick object to process
        :param max_history: Maximum number of historical prices to keep in Redis
        """
        symbol = tick.symbol
        channel = symbol
        history_key = f"history:{symbol}"
        payload = tick.model_dump_json()

        # Using a pipeline to ensure atomicity and reduce network round-trips
        async with self._db.pipeline(transaction=True) as pipe:
            # 1. Distribute the tick to all subscribers (Signal Engines)
            await pipe.publish(channel, payload)

            # 2. Update the historical price list for strategy warm-up
            await pipe.lpush(history_key, tick.price)

            # 3. Trim the list to prevent memory leaks in Redis
            await pipe.ltrim(history_key, 0, max_history - 1)

            await pipe.execute()