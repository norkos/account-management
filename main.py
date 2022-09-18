from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import uuid

app = FastAPI()


class Account(BaseModel):
    name: str | None = None
    email: str | None = None


accounts = {
    uuid.uuid4().hex: {"name": 'my name is foo', 'email': 'nk@wp.pl'},
    uuid.uuid4().hex: {"name": 'my name is bar', 'email': 'bk@wp.pl'},
    uuid.uuid4().hex: {"name": 'my name is tar', 'email': 'ck@wp.pl'}
}


@app.get("/")
async def root():
    return accounts


@app.get('/accounts/{account_uuid}', response_model=Account)
async def read_account(account_uuid: str):
    return accounts[account_uuid]


@app.get('/accounts')
async def read_account():
    return accounts


@app.put('/accounts', response_model=Account)
async def create_account(account: Account):
    updated_item_encoded = jsonable_encoder(account)
    accounts[uuid.uuid4().hex] = updated_item_encoded
    return updated_item_encoded


@app.delete('/accounts/{account_uuid}', response_model=Account)
async def delete_account(account_uuid: str):
    return accounts.pop(account_uuid)


@app.patch('/accounts/{account_uuid}', response_model=Account)
async def update_account(account_uuid: str, account: Account):
    stored_item_data = accounts[account_uuid]
    store_item_model = Account(**stored_item_data)
    update_data = account.dict(exclude_unset=True)
    updated_item = store_item_model.copy(update=update_data)
    accounts[account_uuid] = jsonable_encoder(updated_item)
    return updated_item

