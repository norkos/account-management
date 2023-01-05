import logging
from uuid import UUID

from fastapi import Depends
from fastapi import APIRouter, status
from fastapi_pagination import paginate

from acm_service.data_base.schemas import Agent, AgentCreate
from acm_service.utils.http_exceptions import raise_not_found, raise_email_already_used, raise_bad_request
from acm_service.dependencies import get_token_header, get_agent_dal, get_account_dal
from acm_service.data_base.repositories import AgentRepository, AccountRepository
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.events.producer import EventProducer, get_event_producer
from acm_service.utils.pagination import Page
from acm_service.services.agent_service import AgentService
from acm_service.services.utils import DuplicatedMailException, InconsistencyException

logger = logging.getLogger(DEFAULT_LOGGER)

router = APIRouter(
    tags=["agents"],
    dependencies=[Depends(get_token_header)]
)


@router.get('/accounts/{account_id}/agents/{agent_id}', response_model=Agent)
async def read_agent(agent_id: UUID, agents: AgentRepository = Depends(get_agent_dal),
                     accounts: AccountRepository = Depends(get_account_dal),
                     rabbit_producer: EventProducer = Depends(get_event_producer)):
    agent = await AgentService(agents, accounts, rabbit_producer).get(agent_id)
    if not agent:
        raise_not_found(f'Agent {agent_id} not found')
    return agent


@router.post('/agents/block_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def block_agent(agent_id: UUID,
                      agents: AgentRepository = Depends(get_agent_dal),
                      accounts: AccountRepository = Depends(get_account_dal),
                      rabbit_producer: EventProducer = Depends(get_event_producer)):
    result = await AgentService(agents, accounts, rabbit_producer).block_agent(agent_id)
    if not result:
        raise_not_found(f'Agent {agent_id} not found')


@router.post('/agents/unblock_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def unblock_agent(agent_id: UUID, agents: AgentRepository = Depends(get_agent_dal),
                        accounts: AccountRepository = Depends(get_account_dal),
                        rabbit_producer: EventProducer = Depends(get_event_producer)):
    result = await AgentService(agents, accounts, rabbit_producer).unblock_agent(agent_id)
    if not result:
        raise_not_found(f'Agent {agent_id} not found')


@router.post('/agents/find_agent/{email}', response_model=Agent)
async def find_agent(email: str,
                     agents: AgentRepository = Depends(get_agent_dal),
                     accounts: AccountRepository = Depends(get_account_dal),
                     rabbit_producer: EventProducer = Depends(get_event_producer)):
    agent = await AgentService(agents, accounts, rabbit_producer).get_agent_by_email(email)
    if not agent:
        raise_not_found(f'Agent {email} not found')
    return agent


@router.get('/accounts/{account_id}/agents', response_model=Page[Agent])
async def read_agents(account_id: UUID, agents: AgentRepository = Depends(get_agent_dal),
                      accounts: AccountRepository = Depends(get_account_dal),
                      rabbit_producer: EventProducer = Depends(get_event_producer)):
    agents = await AgentService(agents, accounts, rabbit_producer).get_agents_for_account(account_id)
    return paginate(agents)


@router.get('/agents', response_model=Page[Agent])
async def read_all_agents(agents: AgentRepository = Depends(get_agent_dal),
                          accounts: AccountRepository = Depends(get_account_dal),
                          rabbit_producer: EventProducer = Depends(get_event_producer)):
    agents = await AgentService(agents, accounts, rabbit_producer).get_all()
    return paginate(agents)


@router.post('/accounts/{account_id}/agents', response_model=Agent)
async def create_agent(account_id: UUID, agent: AgentCreate,
                       agents: AgentRepository = Depends(get_agent_dal),
                       accounts: AccountRepository = Depends(get_account_dal),
                       rabbit_producer: EventProducer = Depends(get_event_producer)):
    try:
        return await AgentService(agents, accounts, rabbit_producer).create_agent(
            name=agent.name, email=agent.email, account_id=account_id)
    except DuplicatedMailException:
        raise_email_already_used()


@router.delete('/accounts/{account_id}/agents/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_agent(account_id: UUID, agent_id: UUID,
                       agents: AgentRepository = Depends(get_agent_dal),
                       accounts: AccountRepository = Depends(get_account_dal),
                       rabbit_producer: EventProducer = Depends(get_event_producer)):

    try:
        return await AgentService(agents, accounts, rabbit_producer).delete_agent(
            account_id, agent_id)
    except InconsistencyException:
        raise_bad_request()
