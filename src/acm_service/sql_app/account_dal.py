from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import delete, update
from typing import List
from acm_service.sql_app.models import Account
from uuid import uuid4


class AccountDAL:

    def __init__(self, session: Session):
        self._session = session

    async def create(self, **kwargs) -> Account:
        new_account = Account(id=str(uuid4()), **kwargs)
        self._session.add(new_account)
        await self._session.commit()

        return new_account

    async def get(self, uuid: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.id == uuid))
        return query.scalar()

    async def get_account_by_email(self, email: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.email == email))
        return query.scalar()

    async def get_all(self) -> List[Account]:
        query = await self._session.execute(select(Account).order_by(Account.name))
        return query.scalars().all()

    async def delete(self, uuid: str):
        await self._session.execute(delete(Account).where(Account.id == uuid))
        await self._session.commit()

    async def update(self, uuid: str, **kwargs):
        query = update(Account).where(Account.id == uuid).values(**kwargs).\
            execution_options(synchronize_session="fetch")
        await self._session.execute(query)
        await self._session.flush()
        return await self.get(uuid)
