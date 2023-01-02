import logging
from datetime import timedelta

from uuid import UUID

from aioredis import Redis

from acm_service.data_base.account_dal import AccountDAL
from acm_service.data_base.agent_dal import AgentDAL
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.schemas import Agent, Account, AccountWithoutAgents
from acm_service.utils.env import REDIS_CACHE_INVALIDATION_IN_SECONDS

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


class AccountCachedDAL(AccountDAL):

    def __init__(self, cache: Cache = Cache.get_instance()):
        super().__init__()
        self._cache = cache

    async def update_cache(self, account: AccountWithoutAgents) -> None:
        await self._cache.set(Account.__name__, str(account.id), account.json(),
                              timedelta(seconds=REDIS_CACHE_INVALIDATION_IN_SECONDS))
        logger.debug(f'Putting Account {account.id} into cache')

    async def get_from_cache(self, key: UUID) -> Account | None:
        from_cache = await self._cache.get(Account.__name__, str(key))
        if from_cache is None:
            logger.debug('Cache miss')
            return None
        logger.debug('Cache hit')
        return Account.parse_raw(from_cache)

    async def get(self, account_uuid: UUID) -> Account | None:
        from_cache = await self.get_from_cache(account_uuid)
        if from_cache:
            return from_cache

        result = await super().get(account_uuid)
        if result:
            await self.update_cache(result)

        return result


class AgentCachedDAL(AgentDAL):

    def __init__(self, cache: Cache = Cache.get_instance()):
        super().__init__()
        self._cache = cache

    async def update_cache(self, agent: Agent) -> None:
        await self._cache.set(Agent.__name__, str(agent.id), agent.json(),
                              timedelta(seconds=REDIS_CACHE_INVALIDATION_IN_SECONDS))
        logger.debug(f'Putting Agent {agent.id} into cache')

    async def get_from_cache(self, key: UUID) -> Agent | None:
        from_cache = await self._cache.get(Agent.__name__, str(key))
        if from_cache is None:
            logger.debug('Cache miss')
            return None
        logger.debug('Cache hit')
        return Agent.parse_raw(from_cache)

    async def get(self, agent_uuid: UUID) -> Agent | None:
        from_cache = await self.get_from_cache(agent_uuid)
        if from_cache:
            return from_cache

        result = await super().get(agent_uuid)
        if result:
            await self.update_cache(result)

        return result
