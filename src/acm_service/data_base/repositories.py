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

from sqlalchemy.orm import selectinload, joinedload, Session

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.database import async_session

logger = logging.getLogger(DEFAULT_LOGGER)


def db_session(coro):
    async def wrapper(*args, **kwargs):
        try:
            async with async_session() as session:
                async with session.begin():
                    args[0].set_session(session)
                    return await coro(*args, **kwargs)
        except BaseException as exc:
            logger.exception("DataBase exception %s", exc)
            raise exc

    return wrapper


# todo add more methods
class AbstractRepository(abc.ABC):
    async def get(self, reference):
        raise NotImplementedError

    async def get_all(self):
        raise NotImplementedError


class AgentRepository(AbstractRepository):

    def __init__(self, session: Session = None):
        self._session = session

    def set_session(self, session: Session):
        self._session = session

    @db_session
    async def get(self, agent_uuid: UUID) -> Agent | None:
        query = await self._session.execute(select(AgentDB).where(AgentDB.id == str(agent_uuid)))
        result = query.scalar()
        if result:
            return Agent.from_orm(result)
        return None

    @db_session
    async def get_all(self):
        query = await self._session.execute(select(AgentDB).order_by(AgentDB.name))
        return query.scalars().all()

    @db_session
    async def create(self, **kwargs) -> Agent:
        new_agent = AgentDB(id=str(uuid4()), **kwargs)
        self._session.add(new_agent)
        await self._session.commit()
        return Agent.from_orm(new_agent)

    @db_session
    async def get_agent_by_email(self, email: str) -> Agent | None:
        query = await self._session.execute(select(AgentDB).where(AgentDB.email == email))
        result = query.scalar()
        if result:
            return Agent.from_orm(result)
        return None

    @db_session
    async def get_agents_for_account(self, agent_uuid: UUID) -> List[Agent]:
        query = await self._session.execute(select(AgentDB).where(AgentDB.account_id == str(agent_uuid))
                                            .order_by(AgentDB.name))
        return query.scalars().all()

    @db_session
    async def delete(self, agent_uuid: UUID) -> None:
        await self._session.execute(delete(AgentDB).where(AgentDB.id == str(agent_uuid)))
        await self._session.commit()

    @db_session
    async def delete_all(self) -> None:
        await self._session.execute(delete(AgentDB))

    @db_session
    async def update(self, agent_uuid: UUID, **kwargs) -> None:

        query = update(AgentDB).where(AgentDB.id == str(agent_uuid)).values(**kwargs). \
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()


class AccountRepository(AbstractRepository):

    @db_session
    async def get(self, account_uuid: UUID) -> AccountWithoutAgents | None:
        query = await self._session.execute(select(AccountDB).where(AccountDB.id == str(account_uuid)))
        result = query.scalar()
        if result:
            return AccountWithoutAgents.from_orm(result)
        return None

    @db_session
    async def get_all(self) -> List[AccountWithoutAgents]:
        query = await self._session.execute(select(AccountDB).order_by(AccountDB.name))  # todo from ORM
        return query.scalars().all()

    def __init__(self, session: Session = None):
        self._session = session

    def set_session(self, session: Session):
        self._session = session

    @db_session
    async def create(self, **kwargs) -> AccountWithoutAgents:
        new_account = AccountDB(id=str(uuid4()), **kwargs)
        self._session.add(new_account)
        await self._session.commit()
        return AccountWithoutAgents.from_orm(new_account)

    @db_session
    async def get_with_agents(self, account_uuid: UUID) -> Account | None:
        query = await self._session.execute(select(AccountDB).where(AccountDB.id == str(account_uuid)).
                                            options(selectinload(AccountDB.agents)))
        result = query.scalar()
        if result:
            return Account.from_orm(result)
        return None

    @db_session
    async def get_account_by_email(self, email: str) -> AccountWithoutAgents | None:
        query = await self._session.execute(select(AccountDB).where(AccountDB.email == email))
        result = query.scalar()
        if result:
            return AccountWithoutAgents.from_orm(result)
        return None

    @db_session
    async def delete_all(self) -> None:
        await self._session.execute(delete(AccountDB))

    @db_session
    async def delete(self, account_uuid: UUID) -> None:
        request = select(AccountDB).where(AccountDB.id == str(account_uuid)).options(joinedload(AccountDB.agents))
        account = await self._session.scalar(request)
        await self._session.delete(account)
        await self._session.commit()

    @db_session
    async def update(self, account_uuid: UUID, **kwargs) -> None:
        query = update(AccountDB).where(AccountDB.id == str(account_uuid)).values(**kwargs). \
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()

    @db_session
    async def close(self) -> None:
        if self._session and self._session.is_active:
            await self._session.close()
