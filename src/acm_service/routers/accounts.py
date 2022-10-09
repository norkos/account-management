from fastapi import Depends, HTTPException, Header
from fastapi import APIRouter
from sqlalchemy.orm import Session

from acm_service.sql_app import crud
from acm_service.sql_app import schemas
from acm_service.sql_app.database import SessionLocal
from acm_service.utils.env import API_TOKEN
from acm_service.utils.email_checker import check
from acm_service.utils.publish import RabbitPublisher
from acm_service.utils.http_exceptions import raise_not_found, raise_bad_request

producer = RabbitPublisher()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_token_header(x_token: str = Header()):
    if x_token != API_TOKEN:
        raise_bad_request("Invalid X-Token header")


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(get_token_header)]
)


@router.get('/{account_id}', response_model=schemas.Account)
def read_account(account_id: int, db: Session = Depends(get_db)):
    try:
        db_account = crud.get_account(db, account_id)
    except:
        raise_bad_request()

    if db_account is None:
        raise_not_found('Account not found')

    return db_account


@router.get('/', response_model=list[schemas.Account])
def read_accounts(db: Session = Depends(get_db)):
    accounts = crud.get_accounts(db)
    return accounts


@router.post('/', response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    if not check(account.email):
        raise_bad_request('Invalid email')

    db_account = crud.get_account_by_email(db, account.email)
    if db_account:
        raise_bad_request('Email already used')

    result = crud.create_account(db, account)
    producer.publish('create_account', result.id)

    return result
