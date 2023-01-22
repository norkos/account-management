import logging
from uuid import UUID

from fastapi import Depends
from fastapi import APIRouter, status
from fastapi_pagination import paginate

from acm_service.agents.schema import AgentCreate, Agent
from acm_service.utils.http_exceptions import raise_not_found, raise_email_already_used, raise_bad_request
from acm_service.utils.dependencies import get_token_header, get_agent_service
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.pagination import Page
from acm_service.agents.service import AgentService
from acm_service.utils.http_exceptions import InconsistencyException, DuplicatedMailException

logger = logging.getLogger(DEFAULT_LOGGER)

router = APIRouter(
    tags=["agents"],
    dependencies=[Depends(get_token_header)]
)


@router.get('/accounts/{account_id}/agents/{agent_id}', response_model=Agent)
async def read_agent(agent_id: UUID, agent_service: AgentService = Depends(get_agent_service)):
    agent = await agent_service.get(agent_id)
    if not agent:
        raise_not_found(f'Agent {agent_id} not found')
    return agent


@router.post('/agents/block_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def block_agent(agent_id: UUID, agent_service: AgentService = Depends(get_agent_service)):
    result = await agent_service.block_agent(agent_id)
    if not result:
        raise_not_found(f'Agent {agent_id} not found')


@router.post('/agents/unblock_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def unblock_agent(agent_id: UUID, agent_service: AgentService = Depends(get_agent_service)):
    result = await agent_service.unblock_agent(agent_id)
    if not result:
        raise_not_found(f'Agent {agent_id} not found')


@router.post('/agents/find_agent/{email}', response_model=Agent)
async def find_agent(email: str, agent_service: AgentService = Depends(get_agent_service)):
    agent = await agent_service.get_agent_by_email(email)
    if not agent:
        raise_not_found(f'Agent {email} not found')
    return agent


@router.get('/accounts/{account_id}/agents', response_model=Page[Agent])
async def read_agents(account_id: UUID, agent_service: AgentService = Depends(get_agent_service)):
    agents = await agent_service.get_agents_for_account(account_id)
    return paginate(agents)


@router.get('/agents', response_model=Page[Agent])
async def read_all_agents(agent_service: AgentService = Depends(get_agent_service)):
    agents = await agent_service.get_all()
    return paginate(agents)


@router.post('/accounts/{account_id}/agents', response_model=Agent)
async def create_agent(account_id: UUID, agent: AgentCreate, agent_service: AgentService = Depends(get_agent_service)):
    try:
        result = await agent_service.create_agent(
            name=agent.name, email=agent.email, account_id=account_id)
        return result
    except DuplicatedMailException:
        raise_email_already_used()


@router.delete('/accounts/{account_id}/agents/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_agent(account_id: UUID, agent_id: UUID, agent_service: AgentService = Depends(get_agent_service)):
    try:
        return await agent_service.delete(
            account_id, agent_id)
    except InconsistencyException:
        raise_bad_request()
