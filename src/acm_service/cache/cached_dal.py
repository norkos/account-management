from aioredis import Redis

from acm_service.data_base.account_dal import AccountDAL
from acm_service.data_base.agent_dal import AgentDAL


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

    async def set(self, key: str, value: str):
        await self._redis.set(name=key, value=value)

    async def get(self, key: str) -> str:
        return await self._redis.get(key)


class AccountCachedDAL(AccountDAL):

    def __init__(self, cache: Cache = Cache.get_instance()):
        super().__init__()
        self._cache = cache


class AgentCachedDAL(AgentDAL):

    def __init__(self, cache: Cache = Cache.get_instance()):
        super().__init__()
        self._cache = cache


