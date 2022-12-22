import logging
from typing import Any

from fastapi import Depends
from fastapi import APIRouter, status, Response
from fastapi_pagination import paginate

from acm_service.data_base import schemas
from acm_service.events.producer import EventProducer, get_event_producer
from acm_service.utils.http_exceptions import raise_not_found, raise_bad_request
from acm_service.dependencies import get_account_dal, get_token_header, get_2fa_token_header
from acm_service.data_base.account_dal import AccountDAL
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.pagination import Page

logger = logging.getLogger(DEFAULT_LOGGER)


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(get_token_header)]
)


@router.get('', response_model=Page[schemas.AccountWithoutAgents])
async def read_accounts(accounts: AccountDAL = Depends(get_account_dal)):
    return paginate(await accounts.get_all())


@router.get('/{account_id}', response_model=schemas.AccountWithoutAgents)
async def read_account(account_id: str, accounts: AccountDAL = Depends(get_account_dal)):
    db_account = await accounts.get(account_id)
    if db_account is None:
        raise_not_found(f'Account {account_id} not found')

    return db_account


@router.post('/generate_company_report/{account_id}', response_model=schemas.Account)
async def read_account_with_agents(account_id: str, accounts: AccountDAL = Depends(get_account_dal)):
    db_account = await accounts.get_with_agents(account_id)
    if db_account is None:
        raise_not_found(f'Account {account_id} not found')

    return db_account


@router.delete('/{account_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_account(account_id: str, accounts: AccountDAL = Depends(get_account_dal),
                         rabbit_producer: EventProducer = Depends(get_event_producer)):
    account = await accounts.get_with_agents(account_id)
    if account is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    await accounts.delete(account_id)

    await rabbit_producer.delete_account(region=account.region, account_uuid=account_id, vip=account.vip)
    for agent in schemas.Account.from_orm(account).agents:
        await rabbit_producer.delete_agent(region=account.region, agent_uuid=str(agent.id))
    logger.info(f'Account {account_id} was deleted')


@router.post('/clear', status_code=status.HTTP_202_ACCEPTED)
async def clear(_two_fa_token: Any = Depends(get_2fa_token_header), accounts: AccountDAL = Depends(get_account_dal),
                rabbit_producer: EventProducer = Depends(get_event_producer)):
    await accounts.delete_all()
    await rabbit_producer.delete_account('*', '*', vip=True)
    await rabbit_producer.delete_agent('*', '*')
    logger.info('All accounts were deleted')


@router.post('', response_model=schemas.AccountWithoutAgents)
async def create_account(account: schemas.AccountCreate,
                         accounts: AccountDAL = Depends(get_account_dal),
                         rabbit_producer: EventProducer = Depends(get_event_producer)):
    if await accounts.get_account_by_email(account.email):
        raise_bad_request('E-mail already used')

    result = await accounts.create(name=account.name, email=account.email, region=account.region, vip=account.vip)
    logger.info(f'Account {result.id} was created')

    await rabbit_producer.create_account(region=account.region, account_uuid=result.id, vip=account.vip)
    return result
