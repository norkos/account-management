from sqlalchemy.orm import selectinload, joinedload, Session
from sqlalchemy.future import select
from sqlalchemy import delete, update
from typing import List
from uuid import uuid4
import logging

from acm_service.sql_app.models import Account
from acm_service.utils.logconf import DEFAULT_LOGGER


logger = logging.getLogger(DEFAULT_LOGGER)


def decorate_database(coro):
    async def wrapper(*args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except BaseException as e:
            logger.exception("DataBase exception %s", e)
            raise e
    return wrapper


class AccountDAL:

    def __init__(self, session: Session):
        self._session = session

    @decorate_database
    async def create(self, **kwargs) -> Account:
        new_account = Account(id=str(uuid4()), **kwargs)
        self._session.add(new_account)
        await self._session.commit()

        return new_account

    @decorate_database
    async def get(self, uuid: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.id == uuid))
        return query.scalar()

    @decorate_database
    async def get_with_agents(self, uuid: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.id == uuid).
                                            options(selectinload(Account.agents)))
        return query.scalar()

    @decorate_database
    async def get_account_by_email(self, email: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.email == email))
        return query.scalar()

    @decorate_database
    async def get_all(self) -> List[Account]:
        query = await self._session.execute(select(Account).order_by(Account.name))
        return query.scalars().all()

    @decorate_database
    async def delete_all(self):
        await self._session.execute(delete(Account))

    @decorate_database
    async def delete(self, uuid: str):
        request = select(Account).where(Account.id == uuid).options(joinedload(Account.agents))
        account = await self._session.scalar(request)
        await self._session.delete(account)
        await self._session.commit()

    @decorate_database
    async def update(self, uuid: str, **kwargs):
        query = update(Account).where(Account.id == uuid).values(**kwargs).\
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()

    @decorate_database
    async def close(self):
        if self._session and self._session.is_active:
            await self._session.close()
