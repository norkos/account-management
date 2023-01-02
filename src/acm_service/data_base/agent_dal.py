import logging
from typing import List
from uuid import uuid4, UUID

from sqlalchemy.future import select
from sqlalchemy import delete, update

from acm_service.data_base.models import Agent as AgentDB
from acm_service.data_base.schemas import Agent as Agent
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.database import async_session

logger = logging.getLogger(DEFAULT_LOGGER)


def db_session(coro):
    async def wrapper(*args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except BaseException as exc:
            logger.exception("DataBase exception %s", exc)
            raise exc

    return wrapper


class AgentDAL:

    @db_session
    async def create(self, **kwargs) -> Agent:
        async with async_session() as session:
            async with session.begin():
                new_agent = AgentDB(id=str(uuid4()), **kwargs)
                session.add(new_agent)
                await session.commit()
                return Agent.from_orm(new_agent)

    @db_session
    async def get(self, agent_uuid: UUID) -> Agent | None:
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).where(AgentDB.id == str(agent_uuid)))
                result = query.scalar()
                if result:
                    return Agent.from_orm(result)
                return None

    @db_session
    async def get_agents(self):
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).order_by(AgentDB.name))
                return query.scalars().all()

    @db_session
    async def get_agent_by_email(self, email: str) -> Agent | None:
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).where(AgentDB.email == email))
                result = query.scalar()
                if result:
                    return Agent.from_orm(result)
                return None

    @db_session
    async def get_agents_for_account(self, agent_uuid: UUID) -> List[Agent]:
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).where(AgentDB.account_id == str(agent_uuid))
                                              .order_by(AgentDB.name))
                return query.scalars().all()

    @db_session
    async def delete(self, agent_uuid: UUID) -> None:
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(AgentDB).where(AgentDB.id == str(agent_uuid)))
                await session.commit()

    @db_session
    async def delete_all(self) -> None:
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(AgentDB))

    @db_session
    async def update(self, agent_uuid: UUID, **kwargs) -> None:
        async with async_session() as session:
            async with session.begin():
                query = update(AgentDB).where(AgentDB.id == str(agent_uuid)).values(**kwargs). \
                    execution_options(synchronize_session="fetch")
                await session.execute(query)
                await session.flush()
