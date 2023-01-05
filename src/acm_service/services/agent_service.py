import logging
from uuid import UUID

from fastapi import status, Response

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.repositories import AccountRepository, AgentRepository
from acm_service.events.producer import EventProducer
from acm_service.data_base.schemas import Agent
from acm_service.services.utils import DuplicatedMailException, InconsistencyException

logger = logging.getLogger(DEFAULT_LOGGER)


class AgentService:

    def __init__(self, agents: AgentRepository,
                 accounts: AccountRepository,
                 event_producer: EventProducer):
        self._agents = agents
        self._accounts = accounts
        self._producer = event_producer

    def get_account_repository(self) -> AccountRepository:
        return self._accounts

    async def get(self, agent_id: UUID) -> Agent | None:
        return await self._agents.get(agent_id)

    async def block_agent(self, agent_uuid: UUID) -> bool:
        logger.info(f'Getting agent to be blocked {agent_uuid}')
        agent = await self._agents.get(agent_uuid)
        if agent is None:
            return False

        region = (await self._accounts.get(agent.account_id)).region
        await self._agents.update(agent_uuid, blocked=True)
        await self._producer.block_agent(region, agent_uuid)
        return True

    async def unblock_agent(self, agent_uuid: UUID) -> bool:
        logger.info(f'Getting agent to be unblocked {agent_uuid}')
        agent = await self._agents.get(agent_uuid)
        if agent is None:
            return False

        region = (await self._accounts.get(agent.account_id)).region
        await self._agents.update(agent_uuid, blocked=False)
        await self._producer.unblock_agent(region, agent_uuid)
        return True

    async def get_agent_by_email(self, email: str):
        return await self._agents.get_agent_by_email(email)

    async def get_agents_for_account(self, account_id: UUID):
        return await self._agents.get_agents_for_account(account_id)

    async def get_all(self):
        return await self._agents.get_all()

    async def create_agent(self, name: str, email: str, account_id: UUID) -> Agent:
        if await self._agents.get_agent_by_email(email):
            raise DuplicatedMailException()

        result = await self._agents.create(name=name, email=email, account_id=str(account_id), blocked=False)
        logger.info(f'Agent {result.id} was created')

        account = await self._accounts.get(account_id)

        await self._producer.create_agent(region=account.region, agent_uuid=result.id)
        return Agent.from_orm(result)

    async def delete_agent(self, account_id, agent_id):
        agent = await self._agents.get(agent_id)
        account = await self._accounts.get(account_id)

        if agent is None:
            return

        if account is None or account.id != agent.account_id:
            logger.info(f'Trying to remove agent {agent_id} from the account f{account_id} but they are not linked.')
            raise InconsistencyException()

        await self._agents.delete(agent_id)

        await self._producer.delete_agent(region=account.region, agent_uuid=agent_id)
        logger.info(f'Agent {agent_id} was deleted')
