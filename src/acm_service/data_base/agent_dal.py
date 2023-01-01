import logging
from typing import List
from uuid import uuid4

from sqlalchemy.future import select
from sqlalchemy import delete, update

from acm_service.data_base.models import Agent
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
                new_agent = Agent(id=str(uuid4()), **kwargs)
                session.add(new_agent)
                await session.commit()
                return new_agent

    @db_session
    async def get(self, agent_uuid: str) -> Agent | None:
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(Agent).where(Agent.id == agent_uuid))
                return query.scalar()

    @db_session
    async def get_agents(self):
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(Agent).order_by(Agent.name))
                return query.scalars().all()

    @db_session
    async def get_agent_by_email(self, email: str) -> Agent | None:
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(Agent).where(Agent.email == email))
                return query.scalar()

    @db_session
    async def get_agents_for_account(self, agent_uuid: str) -> List[Agent]:
        async with async_session() as session:
            async with session.begin():
                query = await session.execute(select(Agent).where(Agent.account_id == agent_uuid).order_by(Agent.name))
                return query.scalars().all()

    @db_session
    async def delete(self, agent_uuid: str):
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(Agent).where(Agent.id == agent_uuid))
                await session.commit()

    @db_session
    async def delete_all(self):
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(Agent))

    @db_session
    async def update(self, agent_uuid: str, **kwargs):
        async with async_session() as session:
            async with session.begin():
                query = update(Agent).where(Agent.id == agent_uuid).values(**kwargs). \
                    execution_options(synchronize_session="fetch")
                await session.execute(query)
                await session.flush()


def get_agent_dal() -> AgentDAL:
    return AgentDAL()
