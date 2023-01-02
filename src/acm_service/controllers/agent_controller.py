import logging
from uuid import UUID

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.data_base.account_dal import AccountDAL
from acm_service.data_base.agent_dal import AgentDAL
from acm_service.events.producer import EventProducer

logger = logging.getLogger(DEFAULT_LOGGER)


class AgentController:

    def __init__(self, agents: AgentDAL, accounts: AccountDAL, event_producer: EventProducer):
        self._agents = agents
        self._accounts = accounts
        self._producer = event_producer

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
