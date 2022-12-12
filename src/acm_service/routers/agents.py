import logging
from typing import Any

from fastapi import Depends
from fastapi import APIRouter, status, Response
from fastapi_pagination import paginate

from acm_service.sql_app.schemas import Agent, AgentCreate
from acm_service.utils.http_exceptions import raise_not_found, raise_bad_request
from acm_service.dependencies import get_agent_dal, get_rabbit_producer, get_token_header, get_2fa_token_header, \
    get_account_dal
from acm_service.sql_app.agent_dal import AgentDAL
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.events.producer import RabbitProducer
from acm_service.utils.pagination import Page
from acm_service.controllers.agent_controller import AgentController
from acm_service.sql_app.account_dal import AccountDAL

logger = logging.getLogger(DEFAULT_LOGGER)

router = APIRouter(
    tags=["agents"],
    dependencies=[Depends(get_token_header)]
)


@router.get('/accounts/{account_id}/agents/{agent_id}', response_model=Agent)
async def read_agent(agent_id: str, agents: AgentDAL = Depends(get_agent_dal)):
    agent = await agents.get(agent_id)
    if agent is None:
        raise_not_found(f'Agent {agent_id} not found')

    return agent


@router.post('/agents/block_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def block_agent(agent_id: str, agents: AgentDAL = Depends(get_agent_dal),
                      accounts: AccountDAL = Depends(get_account_dal),
                      rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    result = await AgentController(agents, accounts, rabbit_producer).block_agent(agent_id)

    if not result:
        raise_not_found(f'Agent {agent_id} not found')


@router.post('/agents/unblock_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def unblock_agent(agent_id: str, agents: AgentDAL = Depends(get_agent_dal),
                        accounts: AccountDAL = Depends(get_account_dal),
                        rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    result = await AgentController(agents, accounts, rabbit_producer).unblock_agent(agent_id)

    if not result:
        raise_not_found(f'Agent {agent_id} not found')


@router.post('/agents/find_agent/{email}', response_model=Agent)
async def find_agent(email: str,
                     agents: AgentDAL = Depends(get_agent_dal)):
    agent = await agents.get_agent_by_email(email)
    if agent is None:
        raise_not_found(f'Agent {email} not found')

    return agent


@router.get('/accounts/{account_id}/agents', response_model=Page[Agent])
async def read_agents(account_id: str, agents: AgentDAL = Depends(get_agent_dal)):
    return paginate(await agents.get_agents_for_account(account_id))


@router.get('/agents', response_model=Page[Agent])
async def read_all_agents(database: AgentDAL = Depends(get_agent_dal)):
    return paginate(await database.get_agents())


@router.post('/accounts/{account_id}/agents', response_model=Agent)
async def create_agent(account_id: str, agent: AgentCreate,
                       agents: AgentDAL = Depends(get_agent_dal),
                       accounts: AgentDAL = Depends(get_account_dal),
                       rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    if await agents.get_agent_by_email(agent.email):
        raise_bad_request(f'E-mail {agent.email} is already used')

    result = await agents.create(name=agent.name, email=agent.email, account_id=account_id, blocked=False)
    logger.info(f'Agent {result.id} was created')

    account = await accounts.get(account_id)

    await rabbit_producer.create_agent(region=account.region, agent_uuid=result.id)
    return result


@router.post('/agents/clear', status_code=status.HTTP_202_ACCEPTED)
async def clear(_two_fa_token: Any = Depends(get_2fa_token_header),
                agents: AgentDAL = Depends(get_agent_dal),
                rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    await agents.delete_all()
    await rabbit_producer.delete_agent('*', '*')
    logger.info('All agents were deleted')


@router.delete('/accounts/{account_id}/agents/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_agent(account_id: str, agent_id: str,
                       agents: AgentDAL = Depends(get_agent_dal),
                       accounts: AgentDAL = Depends(get_account_dal),
                       rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    agent = await agents.get(agent_id)
    account = await accounts.get(account_id)

    if agent is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if account is None or account.id != agent.account_id:
        logger.info(f'Trying to remove agent {agent_id} from the account f{account_id} but they are not linked.')
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    await agents.delete(agent_id)

    await rabbit_producer.delete_agent(region=account.region, agent_uuid=agent_id)
    logger.info(f'Agent {agent_id} was deleted')
