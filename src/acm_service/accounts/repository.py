from datetime import timedelta
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import delete, update
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload

from acm_service.accounts.model import Account as AccountDB
from acm_service.accounts.schema import AccountWithoutAgents, Account
from acm_service.utils.cache.repositories import Cache, logger
from acm_service.utils.database.repository import AbstractRepository, log_exception
from acm_service.utils.database.session import create_session
from acm_service.utils.env import REDIS_CACHE_INVALIDATION_IN_SECONDS


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
    async def get_by(self, **kwargs) -> List[AccountWithoutAgents]:
        if 'email' in kwargs.keys():
            return await self.get_account_by_email(kwargs['email'])

        raise NotImplementedError

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
    async def get_account_by_email(self, email: str) -> List[AccountWithoutAgents]:
        async with create_session() as session:
            async with session.begin():
                query = await session.execute(select(AccountDB).where(AccountDB.email == email))
                result = query.scalar()
                if result:
                    return [AccountWithoutAgents.from_orm(result)]
                return []

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


class AccountCachedRepository(AbstractRepository):

    def __init__(self, cache: Cache = Cache.get_instance()):
        self._account_repository = AccountRepository()
        self._cache = cache

    async def update_cache(self, account: AccountWithoutAgents) -> None:
        await self._cache.set(Account.__name__, str(account.id), account.json(),
                              timedelta(seconds=REDIS_CACHE_INVALIDATION_IN_SECONDS))
        logger.debug(f'Putting Account {account.id} into cache')

    async def get_from_cache(self, key: UUID) -> Account | None:
        from_cache = await self._cache.get(Account.__name__, str(key))
        if from_cache is None:
            logger.debug('Cache miss')
            return None
        logger.debug('Cache hit')
        return Account.parse_raw(from_cache)

    async def get(self, account_uuid: UUID) -> AccountWithoutAgents | None:
        from_cache = await self.get_from_cache(account_uuid)
        if from_cache:
            return from_cache

        result = await self._account_repository.get(account_uuid)
        if result:
            await self.update_cache(result)

        return result

    async def get_by(self, **kwargs) -> List[AccountWithoutAgents]:
        return await self._account_repository.get_by(**kwargs)

    async def get_all(self) -> List[AccountWithoutAgents]:
        return await self._account_repository.get_all()

    async def create(self, **kwargs) -> AccountWithoutAgents:
        return await self._account_repository.create(**kwargs)

    async def delete(self, reference) -> None:
        await self._account_repository.delete(reference)

    async def delete_all(self) -> None:
        await self._account_repository.delete_all()

    async def update(self, reference, **kwargs) -> None:
        await self._account_repository.update(reference, **kwargs)
