import asyncio
from typing import Union, AsyncIterator
import redis.asyncio as aioredis


class RedisClient:
    """
    Asynchronous Redis client shared across microservices.
    Handles connections, health checks, and pub/sub messaging.
    """

    def __init__(self):
        # Initializing connection and pubsub as None for async safety
        self._connection: Union[aioredis.Redis, None] = None
        self._pubsub: Union[aioredis.client.PubSub, None] = None

    async def connect(self):
        """
        Establishes an asynchronous connection to the Redis server.

        """
        try:
            # decode_responses=True ensures we get strings (UTF-8) instead of bytes
            # Password must match the Signal Engine configuration
            self._connection = await aioredis.Redis(
                host="localhost",
                password="12345",
                decode_responses=True
            )
            # Initialize pubsub with 'ignore_subscribe_messages' to filter out metadata
            self._pubsub = self._connection.pubsub(ignore_subscribe_messages=True)
            print("Successfully connected to Redis.")
        except Exception as e:
            print(f"Redis Connection Error: {e}")

    async def disconnect(self):
        """
        Gracefully closes the Redis connection and pubsub instances.

        """
        if self._pubsub:
            await self._pubsub.aclose()
        if self._connection:
            await self._connection.aclose()
            print("Redis connection closed.")

    async def is_healthy(self) -> bool:
        """
        Checks if the Redis server is responsive.

        """
        try:
            return await self._connection.ping()
        except:
            return False

    async def subscribe(self, *args) -> AsyncIterator[dict]:
        """
        Subscribes to one or more Redis channels.

        """
        if not self._pubsub:
            raise RuntimeError("PubSub not initialized. Call connect() first.")

        # Handle different input formats for channels
        if len(args) == 1 and isinstance(args[0], (list, tuple, set)):
            channels = args[0]
        else:
            channels = args

        print(f"Subscribing to Redis channels: {channels}")
        await self._pubsub.subscribe(*channels)

        async for message in self._pubsub.listen():
            yield message

    async def get_connection(self) -> aioredis.Redis:
        """
        Returns the raw connection object for use by other handlers (e.g., RedisIngestHandler).

        """
        if not self._connection:
            raise RuntimeError("Connection not established. Call connect() first.")
        return self._connection
