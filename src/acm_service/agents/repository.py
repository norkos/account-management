from datetime import timedelta
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import delete, update
from sqlalchemy.future import select

from acm_service.agents.model import Agent as AgentDB
from acm_service.agents.schema import Agent
from acm_service.utils.cache.repositories import Cache, logger
from acm_service.utils.database.repository import AbstractRepository, log_exception
from acm_service.utils.database.session import create_session
from acm_service.utils.env import REDIS_CACHE_INVALIDATION_IN_SECONDS


class AgentRepository(AbstractRepository):

    @log_exception
    async def get(self, agent_uuid: UUID) -> Agent | None:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).where(AgentDB.id == str(agent_uuid)))
                result = query.scalar()
                if result:
                    return Agent.from_orm(result)
                return None

    @log_exception
    async def get_all(self):
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).order_by(AgentDB.name))
                return query.scalars().all()

    @log_exception
    async def create(self, **kwargs) -> Agent:
        async with create_session() as session:
            async with session.begin():
                new_agent = AgentDB(id=str(uuid4()), **kwargs)
                session.add(new_agent)
                await session.commit()
                return Agent.from_orm(new_agent)

    @log_exception
    async def get_by(self, **kwargs) -> List[Agent]:
        if 'email' in kwargs.keys():
            return await self.get_agent_by_email(kwargs['email'])

        if 'account_id' in kwargs.keys():
            return await self.get_agents_for_account(kwargs['account_id'])

        raise NotImplementedError

    @log_exception
    async def get_agent_by_email(self, email: str) -> List[Agent]:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).where(AgentDB.email == email))
                result = query.scalar()
                if result:
                    return [Agent.from_orm(result)]
                return []

    @log_exception
    async def get_agents_for_account(self, agent_uuid: UUID) -> List[Agent]:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).where(AgentDB.account_id == str(agent_uuid))
                                              .order_by(AgentDB.name))
                return query.scalars().all()

    @log_exception
    async def delete(self, agent_uuid: UUID) -> None:
        async with create_session() as session:
            async with session.begin():
                await session.execute(delete(AgentDB).where(AgentDB.id == str(agent_uuid)))
                await session.commit()

    @log_exception
    async def delete_all(self) -> None:
        async with create_session() as session:
            async with session.begin():
                await session.execute(delete(AgentDB))

    @log_exception
    async def update(self, agent_uuid: UUID, **kwargs) -> None:
        async with create_session() as session:
            async with session.begin():
                query = update(AgentDB).where(AgentDB.id == str(agent_uuid)).values(**kwargs). \
                    execution_options(synchronize_session="fetch")
                await session.execute(query)
                await session.flush()


class AgentCachedRepository(AbstractRepository):

    def __init__(self, cache: Cache = Cache.get_instance()):
        self._agent_repository = AgentRepository()
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

        result = await self._agent_repository.get(agent_uuid)
        if result:
            await self.update_cache(result)

        return result

    async def get_by(self, **kwargs) -> List[Agent]:
        return await self._agent_repository.get_by(**kwargs)

    async def get_all(self) -> List[Agent]:
        return await self._agent_repository.get_all()

    async def create(self, **kwargs) -> Agent:
        return await self._agent_repository.create(**kwargs)

    async def delete(self, reference) -> None:
        await self._agent_repository.delete(reference)

    async def delete_all(self) -> None:
        await self._agent_repository.delete_all()

    async def update(self, reference, **kwargs) -> None:
        await self._agent_repository.update(reference, **kwargs)