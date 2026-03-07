import redis.asyncio as aioredis

class RedisHandler:
    def __init__(self, connection: aioredis.Redis):
        self._db = connection

    async def save_price(self, symbol: str, price: float, max_len: int = 100):
        key = f"history:{symbol}"

        async with self._db.pipeline(transaction=True) as pipe:
            await pipe.lpush(key, price)
            await pipe.ltrim(key, 0, max_len - 1)
            await pipe.execute()

    async def get_prices(self, symbol: str, count: int) -> list[float]:
        key = f"history:{symbol}"
        data = await self._db.lrange(key, 0, count - 1)

        return [float(p) for p in data]

    async def save_tick_with_volume(self, symbol: str, price: float, quantity: int, max_len: int = 100):
        key = f"history_v:{symbol}"
        data = f"{price}:{quantity}"  # שומרים זוג של מחיר וכמות
        async with self._db.pipeline(transaction=True) as pipe:
            await pipe.lpush(key, data)
            await pipe.ltrim(key, 0, max_len - 1)
            await pipe.execute()