import mock
import pytest
from unittest.mock import ANY
from fastapi.testclient import TestClient
from requests import Response

from main import app
from acm_service.routers.accounts import get_account_dal, get_rabbit_producer
from acm_service.utils.env import API_TOKEN, TWO_FA

from .utils import AccountDB, AccountDALStub, RabbitProducerStub

client = TestClient(app)
localDb = AccountDB()


def override_get_db():
    return AccountDALStub(localDb)


def override_get_rabbit_producer():
    return RabbitProducerStub()


app.dependency_overrides[get_account_dal] = override_get_db
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


@mock.patch.object(RabbitProducerStub, 'create_account', autospec=True)
def test_create_account(mocked_method):
    name = 'my_name'
    mail = 'test@mail.com'

    response = create_account(name, mail)
    mocked_method.assert_called_once_with(ANY, account_uuid=response.json()['id'])

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
    create_response = create_account(name, mail)

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


@mock.patch.object(RabbitProducerStub, 'delete_account', autospec=True)
def test_delete_account(mocked_method):
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_account(name, mail)

    account_id = create_response.json()["id"]
    delete_response = client.delete(
        f'/accounts/{account_id}',
        headers={"X-Token": API_TOKEN}
    )
    assert delete_response.status_code == 202
    mocked_method.assert_called_with(ANY, account_uuid=create_response.json()["id"])

    read_response = client.get(
        f'/accounts/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert read_response.status_code == 404
    assert read_response.json() == {"detail": f"Account {account_id} not found"}


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
    assert response.json() == {"detail": "Account 100 not found"}


def test_read_accounts():
    how_many = 20
    for x in range(how_many):
        create_account('my_name', f'test{x}@mail.com')

    response = client.get(
        '/accounts?page=1&size=100',
        headers={"X-Token": API_TOKEN}
    )

    assert response.status_code == 200
    assert len(response.json()['items']) == how_many


def test_read_accounts_bad_token():
    response = client.get(
        '/accounts/',
        headers={"X-Token": "wrong one"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


@mock.patch.object(RabbitProducerStub, 'delete_account', autospec=True)
def test_can_remove_all_accounts(mocked_method):
    create_account('my_name', 'my_mail1@mail.com')
    create_account('my_name', 'my_mail2@mail.com')

    response = client.post(
        f'/accounts/clear',
        headers={"X-Token": API_TOKEN,
                 "TWO-FA": TWO_FA}
    )
    mocked_method.assert_called_with(ANY, account_uuid='*')

    assert response.status_code == 202


def test_cannot_remove_all_accounts():
    create_account('my_name', 'my_mail1@mail.com')
    create_account('my_name2', 'my_mail2@mail.com')

    response = client.post(
        f'/accounts/clear',
        headers={"X-Token": API_TOKEN}
    )

    assert response.status_code == 422
