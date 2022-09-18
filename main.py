from fastapi import Depends, FastAPI, HTTPException, Header
from sql_app import models, schemas, crud
from sql_app.database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

fake_secret_token = "coneofsilence"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {'msg': 'Hello my friend !'}


@app.get('/accounts/{account_id}', response_model=schemas.Account)
def read_account(account_id: int, db: Session = Depends(get_db), x_token: str = Header()):
    if x_token != fake_secret_token:
        raise HTTPException(status_code=400, detail="Invalid X-Token header")

    db_account = crud.get_account(db, account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail='Account not found')
    return db_account


@app.get('/accounts/', response_model=list[schemas.Account])
def read_accounts(db: Session = Depends(get_db), x_token: str = Header()):
    if x_token != fake_secret_token:
        raise HTTPException(status_code=400, detail="Invalid X-Token header")

    accounts = crud.get_accounts(db)
    return accounts


@app.post('/accounts/', response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db), x_token: str = Header()):
    if x_token != fake_secret_token:
        raise HTTPException(status_code=400, detail="Invalid X-Token header")

    db_account = crud.get_account_by_email(db, account.email)
    if db_account:
        raise HTTPException(status_code=400, detail='Email already used')
    return crud.create_account(db, account)
