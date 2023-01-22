import logging
from typing import List
from uuid import UUID

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.database.repository import AbstractRepository
from acm_service.utils.events.producer import EventProducer
from acm_service.accounts.schema import AccountWithoutAgents, Account
from acm_service.utils.http_exceptions import InconsistencyException, DuplicatedMailException

logger = logging.getLogger(DEFAULT_LOGGER)


class AccountService:

    def __init__(self, agents: AbstractRepository,
                 accounts: AbstractRepository,
                 event_producer: EventProducer):
        self._agents = agents
        self._accounts = accounts
        self._producer = event_producer

    async def get_all(self) -> List[AccountWithoutAgents]:
        return await self._accounts.get_all()

    async def get(self, account_id: UUID) -> AccountWithoutAgents | None:
        return await self._accounts.get(account_id)

    async def get_with_agents(self, account_id: UUID) -> Account | None:
        account = await self.get(account_id)
        if account:
            agents = await self._agents.get_by(account_id=account_id)
            result = Account.parse_obj(account.dict())
            result.agents = agents
            return result

        return None

    async def delete(self, account_id: UUID) -> None:
        account = await self.get(account_id)
        if account is None:
            raise InconsistencyException()
        agents = await self._agents.get_by(account_id=account_id)

        await self._accounts.delete(account_id)
        await self._producer.delete_account(region=account.region, account_uuid=account_id, vip=account.vip)
        for agent in agents:
            await self._producer.delete_agent(region=account.region, agent_uuid=agent.id)
        logger.info(f'Account {account_id} was deleted')

    async def create_account(self, name: str, email: str, region: str, vip: bool) -> AccountWithoutAgents:
        if await self.get_account_by_email(email):
            raise DuplicatedMailException()

        result = await self._accounts.create(name=name, email=email, region=region, vip=vip)
        logger.info(f'Account {result.id} was created')

        await self._producer.create_account(region=result.region, account_uuid=result.id, vip=vip)
        return result

    async def delete_all(self) -> None:
        await self._accounts.delete_all()

    async def get_account_by_email(self, email: str) -> AccountWithoutAgents | None:
        result = await self._accounts.get_by(email=email)
        if len(result) == 0:
            return None
        return result[0]
