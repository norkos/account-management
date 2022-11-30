from typing import Any

from fastapi import Depends
from fastapi import APIRouter, status, Response

from fastapi_pagination import paginate

from acm_service.sql_app import schemas
from acm_service.utils.publish import RabbitProducer
from acm_service.utils.http_exceptions import raise_not_found, raise_bad_request
from acm_service.dependencies import get_account_dal, get_rabbit_producer, get_token_header, get_2fa_token_header
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.pagination import Page

import logging

logger = logging.getLogger(DEFAULT_LOGGER)


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(get_token_header)]
)


@router.get('', response_model=Page[schemas.AccountWithoutAgents])
async def read_accounts(database: AccountDAL = Depends(get_account_dal)):
    return paginate(await database.get_all())


@router.get('/{account_id}', response_model=schemas.AccountWithoutAgents)
async def read_account(account_id: str, database: AccountDAL = Depends(get_account_dal)):
    db_account = await database.get(account_id)

    if db_account is None:
        raise_not_found('Account not found')

    return db_account


@router.post('/generate_company_raport/{account_id}', response_model=schemas.Account)
async def read_account_with_agents(account_id: str, database: AccountDAL = Depends(get_account_dal)):
    db_account = await database.get_with_agents(account_id)

    if db_account is None:
        raise_not_found('Account not found')

    return db_account


@router.delete('/{account_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_account(account_id: str, database: AccountDAL = Depends(get_account_dal),
                         rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    if await database.get(account_id) is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    await database.delete(account_id)
    await rabbit_producer.async_publish('delete_account', account_id)

    logger.info(f'Account {account_id} was deleted')


@router.post('/clear', status_code=status.HTTP_202_ACCEPTED)
async def clear(_two_fa_token: Any = Depends(get_2fa_token_header), database: AccountDAL = Depends(get_account_dal),
                rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    await database.delete_all()
    await rabbit_producer.async_publish('delete_account', 'all')
    logger.info(f'All accounts were deleted')


@router.post('', response_model=schemas.AccountWithoutAgents)
async def create_account(account: schemas.AccountCreate, database: AccountDAL = Depends(get_account_dal),
                         rabbit_producer: RabbitProducer = Depends(get_rabbit_producer)):
    if await database.get_account_by_email(account.email):
        raise_bad_request('E-mail already used')

    result = await database.create(name=account.name, email=account.email)
    logger.info(f'Account {result.id} was created')

    await rabbit_producer.async_publish('create_account', result.id)
    return result
