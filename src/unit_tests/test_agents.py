from uuid import uuid4, UUID
from unittest.mock import ANY

import mock
import pytest

from requests import Response

from acm_service.utils.env import AUTH_TOKEN, TWO_FA
from acm_service.data_base.schemas import Agent, Account

from unit_tests.utils import RabbitProducerStub, generate_random_mail
from unit_tests.sut import client, reset_database, account_dal


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    reset_database()


@pytest.fixture
def account() -> Account:
    return account_dal.create_random()


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


@mock.patch.object(RabbitProducerStub, 'create_agent', autospec=True)
def test_create_agent(mocked_method, account):
    name = 'my_name'
    mail = 'test@mail.com'

    response = create_agent(account.id, name, mail)
    mocked_method.assert_called_once_with(ANY, region=account.region, agent_uuid=UUID(response.json()['id']))

    assert response.status_code == 200
    assert response.json()['name'] == name
    assert response.json()['email'] == mail


def test_create_account_duplicated_mail(account):
    duplicate_mail = 'my_mail@mail.com'
    create_agent(account.id, email=duplicate_mail)
    response = create_agent(account.id, email=duplicate_mail)

    assert response.status_code == 400
    assert response.json() == {'detail': f'E-mail {duplicate_mail} is already used'}


@mock.patch.object(RabbitProducerStub, 'block_agent', autospec=True)
def test_block_agent(block_agent, account):
    response = create_agent(account.id)
    agent_uuid = UUID(response.json()['id'])
    is_blocked = response.json()['blocked']

    # not blocked after creation
    assert is_blocked is False

    # when blocking
    response = client.post(
        f'/agents/block_agent/{agent_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )
    block_agent.assert_called_once_with(ANY, region=account.region, agent_uuid=agent_uuid)
    assert response.status_code == 202

    agent = get_agent(account.id, agent_uuid)
    assert agent.blocked


@mock.patch.object(RabbitProducerStub, 'unblock_agent', autospec=True)
def test_unblock_agent(unblock_method, account):
    response = create_agent(account.id)
    agent_uuid = UUID(response.json()['id'])
    client.post(
        f'/agents/block_agent/{agent_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #  when unblocking
    response = client.post(
        f'/agents/unblock_agent/{agent_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )
    unblock_method.assert_called_once_with(ANY, region=account.region, agent_uuid=agent_uuid)
    assert response.status_code == 202

    agent = get_agent(account.id, agent_uuid)
    assert not agent.blocked


def test_create_account_invalid_mail(account):
    response = create_agent(account.id, email='my_mail_mail.com')
    assert response.status_code == 422


def test_create_accounts_bad_token(account):
    response = create_agent(account.id, token='dummy_token')

    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid X-Token header'}


def test_read_agent(account):
    name = 'my_name'
    mail = 'test@mail.com'
    create_response = create_agent(account.id, name, mail)

    read_response = client.get(
        f'/accounts/{account.id}/agents/{create_response.json()["id"]}',
        headers={'X-Token': AUTH_TOKEN}
    )
    assert read_response.status_code == 200
    assert read_response.json() == {
        'id': create_response.json()['id'],
        'name': name,
        'email': mail,
        'account_id': str(account.id),
        'blocked': False
    }


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_delete_agent(mocked_method, account):
    create_response = create_agent(account.id)
    agent_uuid = UUID(create_response.json()['id'])

    delete_response = client.delete(
        f'/accounts/{account.id}/agents/{agent_uuid}',
        headers={"X-Token": AUTH_TOKEN}
    )
    assert delete_response.status_code == 202
    mocked_method.assert_called_with(ANY, region=account.region, agent_uuid=agent_uuid)

    read_response = client.get(
        f'/accounts/{account.id}/agents/{agent_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )
    assert read_response.status_code == 404


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_try_delete_agent_from_other_account(mocked_method, account):
    create_response = create_agent(account.id)

    delete_response = client.delete(
        f'/accounts/{str(uuid4())}/agents/{create_response.json()["id"]}',
        headers={'X-Token': AUTH_TOKEN}
    )
    assert delete_response.status_code == 400
    mocked_method.assert_not_called()


def test_read_agent_bad_token(account):
    create_response = create_agent(account.id)

    read_response = client.get(
        f'/accounts/{account.id}/agents/{create_response.json()["id"]}',
        headers={'X-Token': 'wrong one'}
    )

    assert read_response.status_code == 400
    assert read_response.json() == {"detail": "Invalid X-Token header"}


def test_read_agent_not_found(account):
    random_uuid = uuid4()
    response = client.get(
        f'/accounts/{account.id}/agents/{random_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )
    assert response.status_code == 404
    assert response.json() == {'detail': f'Agent {random_uuid} not found'}


def test_read_agents(account):
    how_many = 20
    for _ in range(how_many):
        create_agent(account.id)

    response = client.get(
        f'/accounts/{account.id}/agents',
        headers={'X-Token': AUTH_TOKEN}
    )

    assert response.status_code == 200
    assert len(response.json()['items']) == how_many


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_can_remove_all_agents(mocked_method, account):
    create_agent(account.id)
    create_agent(account.id)

    response = client.post(
        '/agents/clear',
        headers={'X-Token': AUTH_TOKEN,
                 'TWO-FA': TWO_FA}
    )
    mocked_method.assert_called_with(ANY, region=None, agent_uuid=None)

    assert response.status_code == 202


def test_cannot_remove_all_agents(account):
    create_agent(account.id)
    create_agent(account.id)

    response = client.post(
        '/accounts/clear',
        headers={'X-Token': AUTH_TOKEN}
    )

    assert response.status_code == 422
