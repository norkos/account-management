from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import List
from acm_service.sql_app.models import Account
from uuid import uuid4


class AccountDAL:

    def __init__(self, session: Session):
        self._session = session

    async def create(self, **kwargs) -> Account:
        new_account = Account(id=str(uuid4()), **kwargs)
        self._session.add(new_account)
        await self._session.flush()
        return new_account

    async def get(self, id: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.id == id))
        return query.scalar()

    async def get_account_by_email(self, email: str) -> Account | None:
        query = await self._session.execute(select(Account).where(Account.email == email))
        return query.scalar()

    async def get_all(self) -> List[Account]:
        query = await self._session.execute(select(Account).order_by(Account.name))
        return query.scalars().all()
