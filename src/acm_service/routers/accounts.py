import logging
from uuid import UUID

from fastapi import Depends
from fastapi import APIRouter, status
from fastapi_pagination import paginate

from acm_service.data_base import schemas
from acm_service.utils.http_exceptions import raise_not_found, raise_email_already_used
from acm_service.dependencies import get_token_header, get_account_service
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.pagination import Page
from acm_service.services.account_service import AccountService
from acm_service.services.utils import DuplicatedMailException

logger = logging.getLogger(DEFAULT_LOGGER)

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(get_token_header)]
)


@router.get('', response_model=Page[schemas.AccountWithoutAgents])
async def read_accounts(account_service: AccountService = Depends(get_account_service)):
    result = await account_service.get_all()
    return paginate(result)


@router.get('/{account_id}', response_model=schemas.AccountWithoutAgents)
async def read_account(account_id: UUID, account_service: AccountService = Depends(get_account_service)):
    result = await account_service.get(account_id)
    if result is None:
        raise_not_found(f'Account {account_id} not found')

    return result


@router.post('/generate_company_report/{account_id}', response_model=schemas.Account)
async def generate_company_report(account_id: UUID, account_service: AccountService = Depends(get_account_service)):
    result = await account_service.get_with_agents(account_id)
    if result is None:
        raise_not_found(f'Account {account_id} not found')

    return result


@router.delete('/{account_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_account(account_id: UUID, account_service: AccountService = Depends(get_account_service)):
    await account_service.delete(account_id)


@router.post('', response_model=schemas.AccountWithoutAgents)
async def create_account(account: schemas.AccountCreate,
                         account_service: AccountService = Depends(get_account_service)):
    try:
        return await account_service.create_account(name=account.name,
                                                    email=account.email,
                                                    region=account.region,
                                                    vip=account.vip)

    except DuplicatedMailException:
        raise_email_already_used()
