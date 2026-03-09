from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from redis import asyncio as aioredis

from config import REDIS_URL

redis_client = None

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield
    await redis_client.close()
