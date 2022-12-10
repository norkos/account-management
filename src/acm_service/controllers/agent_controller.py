import logging

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.sql_app.agent_dal import AgentDAL
from acm_service.utils.events.producer import RabbitProducer

logger = logging.getLogger(DEFAULT_LOGGER)


class AgentController:

    def __init__(self, agents: AgentDAL, accounts: AccountDAL, rabbit_producer: RabbitProducer):
        self._agents = agents
        self._accounts = accounts
        self._producer = rabbit_producer

    async def block_agent(self, agent_uuid: str) -> bool:
        logger.info(f'Getting agent {agent_uuid}')
        agent = await self._agents.get(agent_uuid)
        if agent is None:
            logger.info(f'Bye bye')
            return False

        logger.info(f'Show must go on')
        region = (await self._accounts.get(agent.account_id)).region
        await self._agents.update(agent_uuid, blocked=True)
        await self._producer.block_agent(region, agent_uuid)
        return True

    async def unblock_agent(self, agent_uuid: str) -> bool:
        agent = await self._agents.get(agent_uuid)
        if agent is None:
            return False

        region = (await self._accounts.get(agent.account_id)).region
        await self._agents.update(agent_uuid, blocked=False)
        await self._producer.unblock_agent(region, agent_uuid)
        return True
