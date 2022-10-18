from uuid import uuid4
from typing import TypedDict, List
from fastapi.testclient import TestClient

from main import app

from acm_service.routers.accounts import get_db
from acm_service.utils.env import API_TOKEN
from acm_service.sql_app.account_dal import AccountDAL
from sqlalchemy.orm import Session
from acm_service.sql_app.models import Account


class SessionStub(Session):
    pass


class AccountDALStub(AccountDAL):

    def __init__(self):
        super().__init__(SessionStub())
        self._accounts_by_uuid = {}
        self._accounts_by_mail = {}

    async def create(self, **kwargs) -> Account:
        new_account = Account(id=str(uuid4()), **kwargs)
        self._accounts_by_uuid[new_account.id] = new_account
        self._accounts_by_mail[new_account.email] = new_account
        return new_account

    async def get(self, uuid: str) -> Account | None:
        if uuid in self._accounts_by_uuid:
            return self._accounts_by_uuid[uuid]
        return None

    async def get_account_by_email(self, email: str) -> Account | None:
        if email in self._accounts_by_mail:
            return self._accounts_by_mail[email]
        return None

    async def get_all(self) -> List[Account]:
        return list(self._accounts_by_uuid.values())

    async def delete(self, uuid: str):
        if uuid in self._accounts_by_uuid:
            del self._accounts_by_uuid[uuid]
            del self._accounts_by_mail[uuid]

    async def update(self, uuid: str, **kwargs):
        new_account = Account(uuid, **kwargs)
        self._accounts_by_uuid[new_account.id] = new_account
        self._accounts_by_mail[new_account.email] = new_account
        return new_account


def override_get_db():
    return AccountDALStub()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_account():
    response = client.post(
        '/accounts/',
        headers={"X-Token": API_TOKEN},
        json={'name': 'my_name', 'email': 'test@mail.com'}
    )

    assert response.status_code == 200
    assert response.json()['name'] == 'my_name'
    assert response.json()['email'] == 'test@mail.com'


def test_create_account_wrong_mail():
    response = client.post(
        '/accounts/',
        headers={"X-Token": API_TOKEN},
        json={'name': 'my_name', 'email': 'test@mail.com;)'}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid e-mail"}


def test_create_accounts_bad_token():
    response = client.post(
        '/accounts/',
        headers={"X-Token": "wrong one"},
        json={'name': 'my_name', 'email': 'test@mail.com'}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_account():
    response = client.get(
        '/accounts/1',
        headers={"X-Token": API_TOKEN}
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': 1,
        'name': 'my_name',
        'email': 'test@mail.com',
    }


def test_read_account_bad_token():
    response = client.get(
        '/accounts/1',
        headers={"X-Token": "wrong one"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_account_bad_id():
    response = client.get(
        '/accounts/1111111111111111111111111111111111111111111111111111111111111',
        headers={"X-Token": API_TOKEN}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Bad Request"}


def test_read_account_not_found():
    response = client.get(
        '/accounts/100',
        headers={"X-Token": API_TOKEN}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found"}


def test_read_accounts():
    client.post(
        '/accounts/',
        headers={"X-Token": API_TOKEN},
        json={'name': 'my_name', 'email': 'test2@mail.com'}
    )

    client.post(
        '/accounts/',
        headers={"X-Token": API_TOKEN},
        json={'name': 'my_name', 'email': 'test3@mail.com'}
    )

    response = client.get(
        '/accounts/',
        headers={"X-Token": API_TOKEN}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_read_accounts_bad_token():
    response = client.get(
        '/accounts/',
        headers={"X-Token": "wrong one"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}
