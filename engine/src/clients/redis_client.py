import asyncio
from typing import Union, AsyncIterator
import redis.asyncio as aioredis  # Use the asyncio-specific client
from src.clients.base_client import BaseClient
from src.clients.base_subscriber import BaseSubscriber


class RedisClient(BaseClient, BaseSubscriber):
    def __init__(self):
        # Initialize as None; type hinting for the async client
        self._connection: Union[aioredis.Redis, None] = None
        self._pubsub: Union[aioredis.client.PubSub, None] = None

    async def connect(self):
        try:
            # decode_responses=True is vital for getting strings instead of bytes
            self._connection = await aioredis.Redis(
                host="localhost",
                password="12345",
                decode_responses=True
            )

            self._pubsub = self._connection.pubsub(ignore_subscribe_messages=True)
        except Exception as e:
            print(f"Connection Error: {e}")

    async def disconnect(self):
        if self._pubsub:
            await self._pubsub.aclose()  # Always close the pubsub instance
        if self._connection:
            await self._connection.aclose()  # Await the actual connection close

    async def is_healthy(self) -> bool:
        try:
            return await self._connection.ping()
        except:
            return False

    async def subscribe(self, *args) -> AsyncIterator[dict]:
        if not self._pubsub:
            raise RuntimeError("PubSub not initialized. Call connect() first.")

        if len(args) == 1 and isinstance(args[0], (list, tuple, set)):
            channels = args[0]
        else:
            channels = args

        print(f"Subscribing to: {channels}")


        await self._pubsub.subscribe(*channels)

        async for message in self._pubsub.listen():
            yield message

    async def get_connection(self) -> aioredis.Redis:
        if self._connection:
            return self._connection