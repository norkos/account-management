import logging
from datetime import timedelta

from aioredis import Redis

from acm_service.utils.logconf import DEFAULT_LOGGER

logger = logging.getLogger(DEFAULT_LOGGER)


class Cache:
    instance = None

    def __init__(self):
        self._redis = None

    def connect_to_cache_service(self, redis: Redis):
        self._redis = redis

    @classmethod
    def get_instance(cls):
        if Cache.instance is None:
            Cache.instance = Cache()
        return Cache.instance

    async def set(self, namespace: str, key: str, value: str, expiration: timedelta | None):
        await self._redis.set(name=f'{namespace}:{key}', value=value)
        if expiration:
            await self._redis.expire(f'{namespace}:{key}', expiration)

    async def get(self, namespace: str, key: str) -> str | None:
        return await self._redis.get(f'{namespace}:{key}')


