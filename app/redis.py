import redis.asyncio as redis

redis_client = None


class RedisService:
    def __init__(self, url: str):
        self.redis_client = None
        self.url = url

    async def init_redis(self):
        self.redis_client = redis.from_url(self.url, decode_responses=True)

    async def cache_url(self, url: str):
        return await self.redis_client.sadd("visited_urls", url)

    async def is_url_cached(self, url: str):
        return await self.redis_client.sismember("visited_urls", url)

    async def delete_visited_urls(self):
        return await self.redis_client.delete("visited_urls")



redis_service: RedisService = RedisService("redis://localhost:6379")
