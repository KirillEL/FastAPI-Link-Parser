import redis.asyncio as redis

redis_client = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url("redis://5.35.99.226:6379", decode_responses=True)


async def cache_url(url: str):
    return await redis_client.sadd("visited_urls", url)


async def is_url_cached(url: str):
    return await redis_client.sismember("visited_urls", url)


async def delete_visited_urls():
    return await redis_client.delete("visited_urls")
