import asyncio
import datetime

from src.models.schemas.NormalizedTick import NormalizedTick
from test.MockRedisClient import MockRedisClient

async def main():
    mock_tick = NormalizedTick(symbol="AAPL", price=23.2, quantity=3, timestamp=1772382585, received_at=1772382585)

    client = MockRedisClient()
    await client.connect()
    client.subscribe("mock_channel")
    print("Subscribed to channel")
    await asyncio.sleep(2)
    await client.publish(channel="mock_channel", message=mock_tick)
    await asyncio.sleep(2)
    await client.publish(channel="mock_channel", message=mock_tick)
    await client.publish(channel="mock_channel", message=mock_tick)


asyncio.run(main())
