from uuid import uuid4

import mock
import pytest
from unittest.mock import ANY
from fastapi.testclient import TestClient
from requests import Response

from main import app

from acm_service.utils.env import API_TOKEN, TWO_FA
from acm_service.dependencies import get_agent_dal, get_rabbit_producer, get_account_dal

from .utils import AgentDB, AgentDALStub, RabbitProducerStub, AccountDALStub

client = TestClient(app)
localDb = AgentDB()


def override_agent_dal():
    return AgentDALStub(localDb)


account_dal = AccountDALStub(localDb)
def override_account_dal():
    return account_dal


def override_get_rabbit_producer():
    return RabbitProducerStub()


app.dependency_overrides[get_agent_dal] = override_agent_dal
app.dependency_overrides[get_account_dal] = override_account_dal
app.dependency_overrides[get_rabbit_producer] = override_get_rabbit_producer


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    localDb.reset()


def create_agent(account_uuid: str, name: str, email: str) -> Response:
    return client.post(
        f'/accounts/{account_uuid}/agents',
        headers={"X-Token": API_TOKEN},
        json={'name': name, 'email': email}
    )


@mock.patch.object(RabbitProducerStub, 'create_agent', autospec=True)
def test_create_agent(mocked_method):
    account = account_dal.create_random()
    name = 'my_name'
    mail = 'test@mail.com'

    response = create_agent(account.id, name, mail)
    mocked_method.assert_called_once_with(ANY, region=account.region, agent_uuid=response.json()['id'])

    assert response.status_code == 200
    assert response.json()['name'] == name
    assert response.json()['email'] == mail


def test_create_account_duplicated_mail():
    account = account_dal.create_random()

    create_agent(account.id, 'my_name', 'my_mail@mail.com')
    response = create_agent(account.id, 'my_name2', 'my_mail@mail.com')

    assert response.status_code == 400
    assert response.json() == {"detail": "E-mail my_mail@mail.com is already used"}


def test_create_account_invalid_mail():
    account = account_dal.create_random()
    response = create_agent(account.id, 'my_name2', 'my_mailmail.com')
    assert response.status_code == 422


def test_create_accounts_bad_token():
    account = account_dal.create_random()
    response = client.post(
        f'/accounts/${account.id}/agents',
        headers={"X-Token": "wrong one"},
        json={'name': 'my_name', 'email': 'test@mail.com'}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_agent():
    account = account_dal.create_random()
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(account.id, name, mail)

    read_response = client.get(
        f'/accounts/{account.id}/agents/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert read_response.status_code == 200
    assert read_response.json() == {
        'id': create_response.json()['id'],
        'name':  name,
        'email': mail,
        'account_id': account.id
    }


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_delete_agent(mocked_method):
    account = account_dal.create_random()
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(account.id, name, mail)

    delete_response = client.delete(
        f'/accounts/{account.id}/agents/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert delete_response.status_code == 202
    mocked_method.assert_called_with(ANY, region=account.region, agent_uuid=create_response.json()["id"])

    read_response = client.get(
        f'/accounts/{account.id}/agents/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert read_response.status_code == 404


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_try_delete_agent_from_other_account(mocked_method):
    account = account_dal.create_random()
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(account.id, name, mail)

    delete_response = client.delete(
        f'/accounts/{str(uuid4())}/agents/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert delete_response.status_code == 400
    mocked_method.assert_not_called()


def test_read_agent_bad_token():
    account = account_dal.create_random()
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(account.id, name, mail)

    read_response = client.get(
        f'/accounts/{account.id}/agents/{create_response.json()["id"]}',
        headers={"X-Token": 'wrong one'}
    )

    assert read_response.status_code == 400
    assert read_response.json() == {"detail": "Invalid X-Token header"}


def test_read_agent_not_found():
    account = account_dal.create_random()
    response = client.get(
        f'/accounts/{account.id}/agents/100',
        headers={"X-Token": API_TOKEN}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Agent 100 not found"}


def test_read_agents():
    account = account_dal.create_random()
    how_many = 20
    for x in range(how_many):
        create_agent(account.id, 'my_name', f'test{x}@mail.com')

    response = client.get(
        f'/accounts/{account.id}/agents',
        headers={"X-Token": API_TOKEN}
    )

    assert response.status_code == 200
    assert len(response.json()['items']) == how_many


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_can_remove_all_agents(mocked_method):
    account = account_dal.create_random()
    create_agent(account.id, 'my_name', 'my_mail1@mail.com')
    create_agent(account.id, 'my_name', 'my_mail2@mail.com')

    response = client.post(
        f'/agents/clear',
        headers={"X-Token": API_TOKEN,
                 "TWO-FA": TWO_FA}
    )
    mocked_method.assert_called_with(ANY, region='*', agent_uuid='*')

    assert response.status_code == 202


def test_cannot_remove_all_agents():
    account = account_dal.create_random()
    create_agent(account.id, 'my_name', 'my_mail1@mail.com')
    create_agent(account.id, 'my_name2', 'my_mail2@mail.com')

    response = client.post(
        f'/agents/clear',
        headers={"X-Token": API_TOKEN}
    )

    assert response.status_code == 422
