from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import delete, update
from typing import List
from uuid import uuid4

from acm_service.sql_app.models import Agent
from acm_service.utils.logconf import DEFAULT_LOGGER

import logging

logger = logging.getLogger(DEFAULT_LOGGER)


def decorate_database(coro):
    async def wrapper(*args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except BaseException as e:
            logger.error("DataBase exception %s", e)
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
    async def get(self, uuid: str) -> Agent | None:
        query = await self._session.execute(select(Agent).where(Agent.id == uuid))
        return query.scalar()

    @decorate_database
    async def get_agent_by_email(self, email: str) -> Agent | None:
        query = await self._session.execute(select(Agent).where(Agent.email == email))
        return query.scalar()

    @decorate_database
    async def get_agents_for_account(self, uuid: str) -> List[Agent]:
        query = await self._session.execute(select(Agent).where(Agent.account_id == uuid).order_by(Agent.name))
        return query.scalars().all()

    @decorate_database
    async def delete(self, uuid: str):
        await self._session.execute(delete(Agent).where(Agent.id == uuid))
        await self._session.commit()

    @decorate_database
    async def update(self, uuid: str, **kwargs):
        query = update(Agent).where(Agent.id == uuid).values(**kwargs).\
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()
        return await self.get(uuid)

    @decorate_database
    async def close(self):
        if self._session and self._session.is_active:
            await self._session.close()

