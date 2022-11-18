from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import delete, update
from typing import List
from uuid import uuid4

from acm_service.sql_app.models import Account
from acm_service.utils.logconf import DEFAULT_LOGGER

import logging
import decorator

logger = logging.getLogger(DEFAULT_LOGGER)


@decorator.decorator
async def decorate_database(coro, *args, **kwargs):
    try:
        return await coro(*args, **kwargs)
    except BaseException as e:
        logger.error("DataBase exception %s", e)


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
    async def get_account_by_email(self, email: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.email == email))
        return query.scalar()

    @decorate_database
    async def get_all(self) -> List[Account]:
        query = await self._session.execute(select(Account).order_by(Account.name))
        return query.scalars().all()

    @decorate_database
    async def delete(self, uuid: str):
        await self._session.execute(delete(Account).where(Account.id == uuid))
        await self._session.commit()

    @decorate_database
    async def update(self, uuid: str, **kwargs):
        query = update(Account).where(Account.id == uuid).values(**kwargs).\
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()
        return await self.get(uuid)

    async def close(self):
        if self._session and self._session.is_active:
            await self._session.close()
