from fastapi import Depends, HTTPException, Header
from fastapi import APIRouter
from sqlalchemy.orm import Session

from acm_service.sql_app import crud
from acm_service.sql_app import schemas
from acm_service.sql_app.database import SessionLocal
from acm_service.utils.env import API_TOKEN
from acm_service.utils.email_checker import check
from acm_service.utils.publish import RabbitPublisher


producer = RabbitPublisher()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_token_header(x_token: str = Header()):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=400, detail="Invalid X-Token header")


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
        raise HTTPException(status_code=400, detail='Invalid request')

    if db_account is None:
        raise HTTPException(status_code=404, detail='Account not found')
    return db_account


@router.get('/', response_model=list[schemas.Account])
def read_accounts(db: Session = Depends(get_db)):

    accounts = crud.get_accounts(db)
    return accounts


@router.post('/', response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):

    if not check(account.email):
        raise HTTPException(status_code=400, detail="Invalid email")

    db_account = crud.get_account_by_email(db, account.email)
    if db_account:
        raise HTTPException(status_code=400, detail='Email already used')

    result = crud.create_account(db, account)
    producer.publish('create_account', result.id)

    return result