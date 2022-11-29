import mock
import pytest
from unittest.mock import ANY
from fastapi.testclient import TestClient
from requests import Response

from main import app

from acm_service.utils.env import API_TOKEN, TWO_FA
from acm_service.dependencies import get_agent_dal, get_rabbit_producer

from .utils import AgentDB, AgentDALStub, RabbitProducerStub


client = TestClient(app)
localDb = AgentDB()


def override_get_db():
    return AgentDALStub(localDb)


def override_get_rabbit_producer():
    return RabbitProducerStub()


app.dependency_overrides[get_agent_dal] = override_get_db
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


@mock.patch.object(RabbitProducerStub, 'async_publish', autospec=True)
def test_create_agent(mock_async_publish):
    parent_uuid = localDb.create_random_parent()
    name = 'my_name'
    mail = 'test@mail.com'

    response = create_agent(parent_uuid, name, mail)
    mock_async_publish.assert_called_once_with(ANY, method="create_agent", body=response.json()['id'])

    assert response.status_code == 200
    assert response.json()['name'] == name
    assert response.json()['email'] == mail


def test_create_account_duplicated_mail():
    parent_uuid = localDb.create_random_parent()

    create_agent(parent_uuid, 'my_name', 'my_mail@mail.com')
    response = create_agent(parent_uuid, 'my_name2', 'my_mail@mail.com')

    assert response.status_code == 400
    assert response.json() == {"detail": "E-mail already used"}


def test_create_account_invalid_mail():
    parent_uuid = localDb.create_random_parent()
    response = create_agent(parent_uuid, 'my_name2', 'my_mailmail.com')
    assert response.status_code == 422


def test_create_accounts_bad_token():
    parent_uuid = localDb.create_random_parent()
    response = client.post(
        f'/accounts/${parent_uuid}/agents',
        headers={"X-Token": "wrong one"},
        json={'name': 'my_name', 'email': 'test@mail.com'}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_agent():
    parent_uuid = localDb.create_random_parent()
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(parent_uuid, name, mail)

    read_response = client.get(
        f'/accounts/{parent_uuid}/agents/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert read_response.status_code == 200
    assert read_response.json() == {
        'id': create_response.json()['id'],
        'name':  name,
        'email': mail,
        'account_id': parent_uuid
    }


@mock.patch.object(RabbitProducerStub, 'async_publish', autospec=True)
def test_delete_agent(mock_async_publish):
    parent_uuid = localDb.create_random_parent()
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(parent_uuid, name, mail)

    delete_response = client.delete(
        f'/accounts/{parent_uuid}/agents/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert delete_response.status_code == 202
    mock_async_publish.assert_called_with(ANY, method="delete_agent", body=create_response.json()["id"])

    read_response = client.get(
        f'/accounts/{parent_uuid}/agents/{create_response.json()["id"]}',
        headers={"X-Token": API_TOKEN}
    )
    assert read_response.status_code == 404


def test_read_agent_bad_token():
    parent_uuid = localDb.create_random_parent()
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(parent_uuid, name, mail)

    read_response = client.get(
        f'/accounts/{parent_uuid}/agents/{create_response.json()["id"]}',
        headers={"X-Token": 'wrong one'}
    )

    assert read_response.status_code == 400
    assert read_response.json() == {"detail": "Invalid X-Token header"}


def test_read_agent_not_found():
    parent_uuid = localDb.create_random_parent()
    response = client.get(
        f'/accounts/{parent_uuid}/agents/100',
        headers={"X-Token": API_TOKEN}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Agent not found"}


def test_read_agents():
    parent_uuid = localDb.create_random_parent()
    how_many = 20
    for x in range(how_many):
        create_agent(parent_uuid, 'my_name', f'test{x}@mail.com')

    response = client.get(
        f'/accounts/{parent_uuid}/agents',
        headers={"X-Token": API_TOKEN}
    )

    assert response.status_code == 200
    assert len(response.json()['items']) == how_many


@mock.patch.object(RabbitProducerStub, 'async_publish', autospec=True)
def test_can_remove_all_agents(mock_async_publish):
    parent_uuid = localDb.create_random_parent()
    create_agent(parent_uuid, 'my_name', 'my_mail1@mail.com')
    create_agent(parent_uuid, 'my_name', 'my_mail2@mail.com')

    response = client.post(
        f'/agents/clear',
        headers={"X-Token": API_TOKEN,
                 "TWO-FA": TWO_FA}
    )
    mock_async_publish.assert_called_with(ANY, method="delete_agent", body='all')

    assert response.status_code == 202


def test_cannot_remove_all_agents():
    parent_uuid = localDb.create_random_parent()
    create_agent(parent_uuid, 'my_name', 'my_mail1@mail.com')
    create_agent(parent_uuid, 'my_name2', 'my_mail2@mail.com')

    response = client.post(
        f'/agents/clear',
        headers={"X-Token": API_TOKEN}
    )

    assert response.status_code == 422
