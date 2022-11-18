from uuid import uuid4
from typing import List

import mock
import pytest

from unittest.mock import ANY

from sqlalchemy.orm import Session


from fastapi.testclient import TestClient
from requests import Response

from main import app

from acm_service.routers.accounts import get_db, get_rabbit_producer
from acm_service.utils.env import API_TOKEN
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.sql_app.models import Account
from acm_service.utils.publish import RabbitProducer


class LocalDB:
    def __init__(self):
        self._accounts_by_uuid = {}
        self._accounts_by_mail = {}

    @property
    def accounts_by_uuid(self):
        return self._accounts_by_uuid

    @property
    def accounts_by_mail(self):
        return self._accounts_by_mail

    def reset(self):
        self._accounts_by_uuid = {}
        self._accounts_by_mail = {}


class AccountDALStub(AccountDAL):
    class SessionStub(Session):
        pass

    def __init__(self, local_db: LocalDB):
        super().__init__(self.SessionStub())
        self._accounts_by_uuid = local_db.accounts_by_uuid
        self._accounts_by_mail = local_db.accounts_by_mail

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


client = TestClient(app)
localDb = LocalDB()


def override_get_db():
    return AccountDALStub(localDb)


class RabbitProducerStub(RabbitProducer):

    def __init__(self):
        super().__init__('')

    async def async_publish(self, method, body) -> None:
        pass


def override_get_rabbit_producer():
    return RabbitProducerStub()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_rabbit_producer] = override_get_rabbit_producer


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    localDb.reset()


def create_account(name: str, email: str) -> Response:
    return client.post(
        '/accounts',
        headers={"X-Token": API_TOKEN},
        json={'name': name, 'email': email}
    )


@mock.patch.object(RabbitProducerStub, 'async_publish', autospec=True)
def test_create_account(mock_async_publish):
    name = 'my_name'
    mail = 'test@mail.com'

    response = create_account(name, mail)
    mock_async_publish.assert_called_once_with(ANY, method="create_account", body=response.json()['id'])

    assert response.status_code == 200
    assert response.json()['name'] == name
    assert response.json()['email'] == mail


def test_create_account_duplicated_mail():
    create_account('my_name', 'my_mail@mail.com')
    response = create_account('my_name2', 'my_mail@mail.com')

    assert response.status_code == 400
    assert response.json() == {"detail": "E-mail already used"}


def test_create_account_invalid_mail():
    response = create_account('my_name2', 'my_mailmail.com')
    assert response.status_code == 422


def test_create_accounts_bad_token():
    response = client.post(
        '/accounts',
        headers={"X-Token": "wrong one"},
        json={'name': 'my_name', 'email': 'test@mail.com'}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_account():
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_account(name , mail)

    read_response = client.get(
        f'/accounts/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert read_response.status_code == 200
    assert read_response.json() == {
        'id': create_response.json()['id'],
        'name':  name,
        'email': mail,
    }


def test_read_account_bad_token():
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_account(name, mail)

    read_response = client.get(
        f'/accounts/{create_response.json()["id"]}',
        headers={"X-Token": 'wrong one'}
    )

    assert read_response.status_code == 400
    assert read_response.json() == {"detail": "Invalid X-Token header"}


def test_read_account_not_found():
    response = client.get(
        '/accounts/100',
        headers={"X-Token": API_TOKEN}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found"}


def test_read_accounts():
    how_many = 20
    for x in range(how_many):
        create_account('my_name', f'test{x}@mail.com')

    response = client.get(
        '/accounts/',
        headers={"X-Token": API_TOKEN}
    )

    assert response.status_code == 200
    assert len(response.json()) == how_many


def test_read_accounts_bad_token():
    response = client.get(
        '/accounts/',
        headers={"X-Token": "wrong one"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}
