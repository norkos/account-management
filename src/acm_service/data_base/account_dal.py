from typing import List
from uuid import uuid4
import logging

from sqlalchemy.orm import selectinload, joinedload, Session
from sqlalchemy.future import select
from sqlalchemy import delete, update

from acm_service.data_base.models import Account
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


class AccountDAL:

    def __init__(self, session: Session = None):
        self._session = session

    def set_session(self, session: Session):
        self._session = session

    @db_session
    async def create(self, **kwargs) -> Account:
        new_account = Account(id=str(uuid4()), **kwargs)
        self._session.add(new_account)
        await self._session.commit()

        return new_account

    @db_session
    async def get(self, account_uuid: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.id == account_uuid))
        return query.scalar()

    @db_session
    async def get_with_agents(self, account_uuid: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.id == account_uuid).
                                            options(selectinload(Account.agents)))
        return query.scalar()

    @db_session
    async def get_account_by_email(self, email: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.email == email))
        return query.scalar()

    @db_session
    async def get_all(self) -> List[Account]:
        query = await self._session.execute(select(Account).order_by(Account.name))
        return query.scalars().all()

    @db_session
    async def delete_all(self):
        await self._session.execute(delete(Account))

    @db_session
    async def delete(self, account_uuid: str):
        request = select(Account).where(Account.id == account_uuid).options(joinedload(Account.agents))
        account = await self._session.scalar(request)
        await self._session.delete(account)
        await self._session.commit()

    @db_session
    async def update(self, account_uuid: str, **kwargs):
        query = update(Account).where(Account.id == account_uuid).values(**kwargs). \
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()

    @db_session
    async def close(self):
        if self._session and self._session.is_active:
            await self._session.close()
