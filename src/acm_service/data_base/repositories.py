import abc
import logging
from uuid import uuid4, UUID
from typing import List

from sqlalchemy.future import select
from sqlalchemy import delete, update

from acm_service.data_base.models import Agent as AgentDB
from acm_service.data_base.models import Account as AccountDB

from acm_service.data_base.schemas import Agent as Agent
from acm_service.data_base.schemas import Account as Account, AccountWithoutAgents

from sqlalchemy.orm import selectinload, joinedload

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.database import create_session

logger = logging.getLogger(DEFAULT_LOGGER)


def log_exception(coro):
    async def wrap(*args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except BaseException as exc:
            logger.exception("Exception %s", exc)
            raise exc
    return wrap


# todo add more methods
class AbstractRepository(abc.ABC):
    async def get(self, reference):
        raise NotImplementedError

    async def get_all(self):
        raise NotImplementedError


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
    async def get_agent_by_email(self, email: str) -> Agent | None:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AgentDB).where(AgentDB.email == email))
                result = query.scalar()
                if result:
                    return Agent.from_orm(result)
                return None

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


class AccountRepository(AbstractRepository):

    @log_exception
    async def get(self, account_uuid: UUID) -> AccountWithoutAgents | None:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AccountDB).where(AccountDB.id == str(account_uuid)))
                result = query.scalar()
                if result:
                    return AccountWithoutAgents.from_orm(result)
                return None

    @log_exception
    async def get_all(self) -> List[AccountWithoutAgents]:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AccountDB).order_by(AccountDB.name))  # todo from ORM
                return query.scalars().all()

    @log_exception
    async def create(self, **kwargs) -> AccountWithoutAgents:
        async with create_session() as session:
            async with session.begin():
                new_account = AccountDB(id=str(uuid4()), **kwargs)
                session.add(new_account)
                await session.commit()
                return AccountWithoutAgents.from_orm(new_account)

    @log_exception
    async def get_with_agents(self, account_uuid: UUID) -> Account | None:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AccountDB).where(AccountDB.id == str(account_uuid)).
                                              options(selectinload(AccountDB.agents)))
                result = query.scalar()
                if result:
                    return Account.from_orm(result)
                return None

    @log_exception
    async def get_account_by_email(self, email: str) -> AccountWithoutAgents | None:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AccountDB).where(AccountDB.email == email))
                result = query.scalar()
                if result:
                    return AccountWithoutAgents.from_orm(result)
                return None

    @log_exception
    async def delete_all(self) -> None:
        async with create_session() as session:
            async with session.begin():
                await session.execute(delete(AccountDB))

    @log_exception
    async def delete(self, account_uuid: UUID) -> None:
        async with create_session() as session:
            async with session.begin():
                request = select(AccountDB).where(AccountDB.id == str(account_uuid)).options(
                    joinedload(AccountDB.agents))
                account = await session.scalar(request)
                await session.delete(account)
                await session.commit()

    @log_exception
    async def update(self, account_uuid: UUID, **kwargs) -> None:
        async with create_session() as session:
            async with session.begin():
                query = update(AccountDB).where(AccountDB.id == str(account_uuid)).values(**kwargs). \
                    execution_options(synchronize_session="fetch")
                await session.execute(query)
                await session.flush()
