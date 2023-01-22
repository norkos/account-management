from uuid import uuid4, UUID
import mock
import namegenerator
from unit_tests.utils import generate_random_mail
from unittest.mock import ANY

from requests import Response
from pydantic import EmailStr

from fastapi.testclient import TestClient

from acm_service.utils.env import AUTH_TOKEN
from acm_service.agents.schema import Agent
from acm_service.agents.service import AgentService
from acm_service.utils.http_exceptions import InconsistencyException, DuplicatedMailException

from main import app

client = TestClient(app)


def get_agent(account_uuid: UUID, agent_uuid: UUID) -> Agent:
    response = client.get(
        f'/accounts/{account_uuid}/agents/{agent_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )
    data = response.json()
    return Agent(**data)


def create_agent(account_uuid: UUID, name: str = 'dummy', email: str = None, token: str = AUTH_TOKEN) -> Response:
    return client.post(
        f'/accounts/{account_uuid}/agents',
        headers={'X-Token': token},
        json={'name': name, 'email': email if email is not None else generate_random_mail()}
    )


simple_agent = Agent(id=uuid4(),
                     name=namegenerator.gen(),
                     email=EmailStr(generate_random_mail()),
                     blocked=False,
                     account_id=uuid4())


@mock.patch.object(AgentService, AgentService.create_agent.__name__, return_value=simple_agent, autospec=True)
def test_create_agent(mocked_method):
    #   given & when
    response = client.post(
        f'/accounts/{simple_agent.account_id}/agents',
        headers={'X-Token': AUTH_TOKEN},
        json={'name': simple_agent.name, 'email': simple_agent.email})

    #   then
    mocked_method.assert_called_once_with(ANY, name=simple_agent.name,
                                          email=simple_agent.email,
                                          account_id=simple_agent.account_id)

    assert response.status_code == 200
    assert response.json()['name'] == simple_agent.name
    assert response.json()['email'] == simple_agent.email


@mock.patch.object(AgentService, AgentService.create_agent.__name__, autospec=True)
def test_create_agent_duplicated_mail(mocked_method):
    #   given
    mocked_method.side_effect = DuplicatedMailException()

    #   when
    response = client.post(
        f'/accounts/{simple_agent.account_id}/agents',
        headers={'X-Token': AUTH_TOKEN},
        json={'name': simple_agent.name, 'email': simple_agent.email}
    )

    #   then
    assert response.status_code == 400
    assert response.json() == {'detail': 'E-mail is already used'}


def test_create_account_invalid_mail():
    #   given
    email = 'invalid'

    #   when
    response = client.post(
        f'/accounts/{simple_agent.account_id}/agents',
        headers={'X-Token': AUTH_TOKEN},
        json={'name': simple_agent.name, 'email': email})

    #   then
    assert response.status_code == 422


@mock.patch.object(AgentService, AgentService.block_agent.__name__, return_value=simple_agent, autospec=True)
def test_block_agent(mocked_method):
    #   given & when
    response = client.post(
        f'/agents/block_agent/{simple_agent.id}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, agent_id=simple_agent.id)
    assert response.status_code == 202


@mock.patch.object(AgentService, AgentService.unblock_agent.__name__, return_value=simple_agent, autospec=True)
def test_unblock_agent(mocked_method):
    #   given & when
    response = client.post(
        f'/agents/unblock_agent/{simple_agent.id}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, agent_id=simple_agent.id)
    assert response.status_code == 202


def test_create_accounts_bad_token():
    #   given
    token = 'wrong_one'

    #   when
    response = client.post(
        f'/accounts/{simple_agent.account_id}/agents',
        headers={'X-Token': token},
        json={'name': simple_agent.name, 'email': simple_agent.email})

    #   then
    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid X-Token header'}


@mock.patch.object(AgentService, AgentService.get.__name__, return_value=simple_agent, autospec=True)
def test_read_agent(mocked_method):
    #   given & when
    response = client.get(
        f'/accounts/{simple_agent.account_id}/agents/{simple_agent.id}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, agent_id=simple_agent.id)
    assert response.status_code == 200
    assert response.json() == {
        'id': str(simple_agent.id),
        'name': simple_agent.name,
        'email': simple_agent.email,
        'account_id': str(simple_agent.account_id),
        'blocked': simple_agent.blocked
    }


@mock.patch.object(AgentService, AgentService.delete.__name__, return_value=simple_agent, autospec=True)
def test_delete_agent(mocked_method):
    #   given & when
    response = client.delete(
        f'/accounts/{simple_agent.account_id}/agents/{simple_agent.id}',
        headers={"X-Token": AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, account_id=simple_agent.account_id, agent_id=simple_agent.id)
    assert response.status_code == 202


@mock.patch.object(AgentService, AgentService.delete.__name__, return_value=simple_agent, autospec=True)
def test_try_delete_agent_from_other_account(mocked_method):
    #   given
    mocked_method.side_effect = InconsistencyException()
    random_account = str(uuid4())

    #   when
    response = client.delete(
        f'/accounts/{random_account}/agents/{simple_agent.id}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    assert response.status_code == 400


@mock.patch.object(AgentService, AgentService.get.__name__, return_value=simple_agent, autospec=True)
def test_read_agent_bad_token(mocked_method):
    #   given
    token = 'wrong_one'

    #   when
    read_response = client.get(
        f'/accounts/{simple_agent.account_id}/agents/{simple_agent.id}',
        headers={'X-Token': token}
    )

    #   then
    mocked_method.assert_not_called()
    assert read_response.status_code == 400
    assert read_response.json() == {'detail': 'Invalid X-Token header'}


@mock.patch.object(AgentService, AgentService.get.__name__, return_value=None, autospec=True)
def test_read_agent_not_found(_mocked_method):
    #   given
    random_uuid = uuid4()

    #   when
    response = client.get(
        f'/accounts/{random_uuid}/agents/{random_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    assert response.status_code == 404
    assert response.json() == {'detail': f'Agent {random_uuid} not found'}


@mock.patch.object(AgentService, AgentService.get_agents_for_account.__name__,
                   return_value=[simple_agent, simple_agent], autospec=True)
def test_read_agents(mocked_method):
    #   given & when
    response = client.get(
        f'/accounts/{simple_agent.account_id}/agents',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, account_id=simple_agent.account_id)
    assert response.status_code == 200
    assert len(response.json()['items']) == 2
