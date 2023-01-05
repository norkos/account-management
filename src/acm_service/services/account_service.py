import logging

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.repositories import AccountRepository, AgentRepository
from acm_service.events.producer import EventProducer
from acm_service.data_base import schemas
from acm_service.data_base.schemas import AccountWithoutAgents
from acm_service.services.utils import DuplicatedMailException, InconsistencyException

logger = logging.getLogger(DEFAULT_LOGGER)


class AccountService:

    def __init__(self, agents: AgentRepository,
                 accounts: AccountRepository,
                 event_producer: EventProducer):
        self._agents = agents
        self._accounts = accounts
        self._producer = event_producer

    async def get_all(self):
        return await self._accounts.get_all()

    async def get(self, account_id):
        return await self._accounts.get(account_id)

    async def get_with_agents(self, account_id):
        return await self._accounts.get_with_agents(account_id)

    async def delete(self, account_id):
        account = await self._accounts.get_with_agents(account_id)
        if account is None:
            raise InconsistencyException()
        await self._accounts.delete(account_id)

        await self._producer.delete_account(region=account.region, account_uuid=account_id, vip=account.vip)
        for agent in schemas.Account.from_orm(account).agents:
            await self._producer.delete_agent(region=account.region, agent_uuid=agent.id)
        logger.info(f'Account {account_id} was deleted')

    async def create(self, name: str, email: str, region: str, vip: bool) -> AccountWithoutAgents:
        if await self._accounts.get_account_by_email(email):
            raise DuplicatedMailException()

        result = await self._accounts.create(name=name, email=email, region=region, vip=vip)
        logger.info(f'Account {result.id} was created')

        await self._producer.create_account(region=result.region, account_uuid=result.id, vip=vip)
        return result
