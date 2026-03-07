import asyncio
from typing import Any

from src.clients.base_client import BaseClient
from src.clients.base_subscriber import BaseSubscriber
from src.models.dtos.RedisMessage import RedisMessage
from src.models.schemas.NormalizedTick import NormalizedTick


class MockRedisClient(BaseClient, BaseSubscriber):
    def __init__(self):
        self.queue: dict[str, asyncio.Queue] = {}

    async def connect(self):
        self.queue["mock_channel"] = asyncio.Queue()

    async def disconnect(self):
        self.queue.__delitem__("mock_channel")

    async def is_healthy(self) -> bool:
        return type(self.queue["mock_channel"]) == asyncio.Queue

    async def publish(self, channel: str, message: NormalizedTick):
        print(self.queue)
        msg = RedisMessage(type="message", channel=channel, data=message.model_dump_json(), pattern=None)
        return self.queue[channel].put_nowait(msg)

    async def subscribe(self, channel_name: str):
        while True:
            yield await self.queue[channel_name].get()
