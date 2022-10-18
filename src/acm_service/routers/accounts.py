from fastapi import Depends, Header
from fastapi import APIRouter, status, Response

from acm_service.sql_app import schemas
from acm_service.utils.env import API_TOKEN
from acm_service.utils.email_checker import check
from acm_service.utils.publish import RabbitPublisher
from acm_service.utils.http_exceptions import raise_not_found, raise_bad_request
from acm_service.dependencies import get_db
from acm_service.sql_app.account_dal import AccountDAL

producer = RabbitPublisher()


async def get_token_header(x_token: str = Header()):
    if x_token != API_TOKEN:
        raise_bad_request("Invalid X-Token header")


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(get_token_header)]
)


@router.get('/{account_id}', response_model=schemas.Account)
async def read_account(account_id: str, database: AccountDAL = Depends(get_db)):
    db_account = await database.get(account_id)

    if db_account is None:
        raise_not_found('Account not found')

    return db_account


@router.get('/', response_model=list[schemas.Account])
async def read_accounts(database: AccountDAL = Depends(get_db)):
    return await database.get_all()


@router.delete('/', status_code=status.HTTP_202_ACCEPTED)
async def delete_account(account_id: str, database: AccountDAL = Depends(get_db)):
    if await database.get(account_id) is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    await database.delete(account_id)


@router.put('/', response_model=schemas.Account)
async def update_account(account_id: str, account: schemas.AccountCreate, database: AccountDAL = Depends(get_db)):
    if not check(account.email):
        raise_bad_request('Invalid e-mail')

    account = await database.update(account_id, **account.dict())
    return account


@router.post('/', response_model=schemas.Account)
async def create_account(account: schemas.AccountCreate, database: AccountDAL = Depends(get_db)):
    if not check(account.email):
        raise_bad_request('Invalid e-mail')

    db_account = await database.get_account_by_email(account.email)
    if db_account:
        raise_bad_request('E-mail already used')

    result = await database.create(name=account.name, email=account.email)
    #producer.publish('create_account', result.id)

    return result
