import logging
from typing import List
from uuid import uuid4

from sqlalchemy.future import select
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from acm_service.data_base.models import Agent
from acm_service.utils.logconf import DEFAULT_LOGGER


logger = logging.getLogger(DEFAULT_LOGGER)


def decorate_database(coro):
    async def wrapper(*args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except BaseException as exc:
            logger.exception("DataBase exception %s", exc)
            raise exc
    return wrapper


class AgentDAL:

    def __init__(self, session: Session):
        self._session = session

    @decorate_database
    async def create(self, **kwargs) -> Agent:
        new_agent = Agent(id=str(uuid4()), **kwargs)
        self._session.add(new_agent)
        await self._session.commit()
        return new_agent

    @decorate_database
    async def get(self, agent_uuid: str) -> Agent | None:
        query = await self._session.execute(select(Agent).where(Agent.id == agent_uuid))
        return query.scalar()

    @decorate_database
    async def get_agents(self):
        query = await self._session.execute(select(Agent).order_by(Agent.name))
        return query.scalars().all()

    @decorate_database
    async def get_agent_by_email(self, email: str) -> Agent | None:
        query = await self._session.execute(select(Agent).where(Agent.email == email))
        return query.scalar()

    @decorate_database
    async def get_agents_for_account(self, agent_uuid: str) -> List[Agent]:
        query = await self._session.execute(select(Agent).where(Agent.account_id == agent_uuid).order_by(Agent.name))
        return query.scalars().all()

    @decorate_database
    async def delete(self, agent_uuid: str):
        await self._session.execute(delete(Agent).where(Agent.id == agent_uuid))
        await self._session.commit()

    @decorate_database
    async def delete_all(self):
        await self._session.execute(delete(Agent))

    @decorate_database
    async def update(self, agent_uuid: str, **kwargs):
        query = update(Agent).where(Agent.id == agent_uuid).values(**kwargs).\
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()

    @decorate_database
    async def close(self):
        if self._session and self._session.is_active:
            await self._session.close()