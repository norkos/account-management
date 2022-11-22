from fastapi import Depends, Header
from fastapi import APIRouter, status, Response

from acm_service.sql_app.schemas import Agent, AgentCreate
from acm_service.utils.env import API_TOKEN
from acm_service.utils.http_exceptions import raise_not_found, raise_bad_request
from acm_service.dependencies import get_agent_dal, get_rabbit_producer
from acm_service.sql_app.agent_dal import AgentDAL
from acm_service.utils.logconf import DEFAULT_LOGGER

import logging

from acm_service.utils.publish import RabbitProducer

logger = logging.getLogger(DEFAULT_LOGGER)


async def get_token_header(x_token: str = Header()):
    if x_token != API_TOKEN:
        raise_bad_request("Invalid X-Token header")


router = APIRouter(
    tags=["agents"],
    dependencies=[Depends(get_token_header)]
)


@router.get('/accounts/{account_id}/agents/{agent_id}', response_model=Agent)
async def read_agent(agent_id: str, database: AgentDAL = Depends(get_agent_dal)):
    agent = await database.get(agent_id)

    if agent is None:
        raise_not_found('Agent not found')

    return agent


@router.post('/agents/find_agent/{email}', response_model=Agent)
async def read_agent(email: str, database: AgentDAL = Depends(get_agent_dal)):
    agent = await database.get_agent_by_email(email)

    if agent is None:
        raise_not_found('Agent not found')

    return agent


@router.get('/accounts/{account_id}/agents', response_model=list[Agent])
async def read_agents(account_id: str, database: AgentDAL = Depends(get_agent_dal)):
    return await database.get_agents_for_account(account_id)


@router.post('/accounts/{account_id}/agents', response_model=Agent)
async def create_agent(account_id: str, agent: AgentCreate, database: AgentDAL = Depends(get_agent_dal),
                       rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    if await database.get_agent_by_email(agent.email):
        raise_bad_request('E-mail already used')

    result = await database.create(name=agent.name, email=agent.email, account_id=account_id)
    logger.info(f'Agent {result.id} was created')

    await rabbit_producer.async_publish('create_agent', result.id)
    return result


@router.delete('/accounts/{account_id}/agents/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_agent(agent_id: str, database: AgentDAL = Depends(get_agent_dal)):
    if await database.get(agent_id) is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    await database.delete(agent_id)
    logger.info(f'Agent {agent_id} was deleted')


#@router.put('/accounts/{account_id}/agents/{agent_id}', response_model=Agent)
async def update_agent(agent_id: str, agent: AgentCreate,
                       database: AgentDAL = Depends(get_agent_dal)):
    result = await database.update(agent_id, **agent.dict())
    return result

