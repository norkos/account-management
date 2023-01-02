from typing import List
from uuid import uuid4, UUID
import logging

from sqlalchemy.orm import selectinload, joinedload, Session
from sqlalchemy.future import select
from sqlalchemy import delete, update

from acm_service.data_base.models import Account as AccountDB
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.database import async_session

from acm_service.data_base.schemas import Account as Account, AccountWithoutAgents

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


class AccountDAL:

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
    async def get(self, account_uuid: UUID) -> AccountWithoutAgents | None:
        query = await self._session.execute(select(AccountDB).where(AccountDB.id == str(account_uuid)))
        result = query.scalar()
        if result:
            return AccountWithoutAgents.from_orm(result)
        return None

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
    async def get_all(self) -> List[AccountWithoutAgents]:
        query = await self._session.execute(select(AccountDB).order_by(AccountDB.name)) # todo from ORM
        return query.scalars().all()

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
