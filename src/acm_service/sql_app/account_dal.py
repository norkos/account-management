import sqlalchemy
from sqlalchemy import Column, Integer, String
from .database import Base
from sqlalchemy.orm import Session


class AccountDAL():

    @classmethod
    async def create(cls, db_session: Session, **kwargs):
        new_account = cls(**kwargs)
        db_session.add(new_account)

        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

        return new_account

    @classmethod
    async def update(cls, db_session: Session, id: int, **kwargs) -> None:
        query = (
            sqlalchemy.update(cls).where(cls.id == id).values(kwargs).execution_options(synchronize_session="fetch")
        )

        await db_session.execute(query)

        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    @classmethod
    async def get(cls, db_session: Session, id: int):
        query = sqlalchemy.select(cls).where(cls.id == id)
        accounts = await db_session.execute(query)
        (account, ) = accounts.first()
        return account

    @classmethod
    async def get_all(cls, db_session: Session):
        query = sqlalchemy.select(cls)
        accounts = await db_session.execute(query)
        accounts = accounts.scalars().all()
        return accounts

    @classmethod
    async def delete(cls, db_session: Session, id: int):
        query = sqlalchemy.delete(cls).where(cls.id == id)
        await db_session.execute(query)
        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise
        return True


