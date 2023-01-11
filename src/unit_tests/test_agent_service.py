import asyncio
from unittest.mock import ANY
from uuid import uuid4
import mock
import namegenerator
import pytest
from pydantic import ValidationError

from acm_service.data_base.schemas import AccountWithoutAgents
from acm_service. services.agent_service import AgentService
from acm_service.services.utils import DuplicatedMailException, InconsistencyException

from unit_tests.utils import RabbitProducerStub,  AgentRepositoryStub, AccountRepositoryStub


@pytest.fixture
def agent_service() -> AgentService:
    accounts = AccountRepositoryStub()
    accounts.create_random()
    return AgentService(AgentRepositoryStub(), accounts, RabbitProducerStub())


@pytest.fixture
def agent_name() -> str:
    return namegenerator.gen()


@pytest.fixture
def agent_mail() -> str:
    return f'{namegenerator.gen()}@gmail.com'


def get_account(agent_service: AgentService) -> AccountWithoutAgents:
    return asyncio.run((agent_service.get_account_repository().get_all()))[0]


@mock.patch.object(RabbitProducerStub, 'create_agent', autospec=True)
def test_create_agent(mocked_method, agent_name, agent_mail, agent_service):
    #   given
    account = get_account(agent_service)

    #   when
    agent = asyncio.run(agent_service.create(agent_name, agent_mail, account.id))

    #   then
    mocked_method.assert_called_once_with(ANY, region=account.region, agent_uuid=agent.id)


def test_create_agent_duplicated_mail(agent_name, agent_mail, agent_service):
    #   given
    account = get_account(agent_service)
    asyncio.run(agent_service.create(agent_name, agent_mail, account.id))

    #  when && then
    with pytest.raises(DuplicatedMailException):
        asyncio.run(agent_service.create(agent_name + agent_name, agent_mail, account.id))


@mock.patch.object(RabbitProducerStub, 'block_agent', autospec=True)
def test_block_agent(block_agent, agent_name, agent_mail, agent_service):
    #   given
    account = get_account(agent_service)
    agent = asyncio.run(agent_service.create(agent_name, agent_mail, account.id))
    assert agent.blocked is False

    #   when
    asyncio.run(agent_service.block_agent(agent.id))

    #   then
    block_agent.assert_called_once_with(ANY, region=account.region, agent_uuid=agent.id)
    assert asyncio.run(agent_service.get(agent.id)).blocked is True


@mock.patch.object(RabbitProducerStub, 'unblock_agent', autospec=True)
def test_unblock_agent(unblock_method, agent_name, agent_mail, agent_service):
    #   given
    account = get_account(agent_service)
    agent = asyncio.run(agent_service.create(agent_name, agent_mail, account.id))
    asyncio.run(agent_service.block_agent(agent.id))

    #   when
    asyncio.run(agent_service.unblock_agent(agent.id))

    #   then
    unblock_method.assert_called_once_with(ANY, region=account.region, agent_uuid=agent.id)
    assert asyncio.run(agent_service.get(agent.id)).blocked is False


@mock.patch.object(RabbitProducerStub, 'create_agent', autospec=True)
def test_create_agent_invalid_mail(mocked_method, agent_name, agent_service):
    #   given
    account = get_account(agent_service)

    #  when && then
    with pytest.raises(ValidationError):
        asyncio.run(agent_service.create(agent_name, 'agent_mail', account.id))

    #   then
    mocked_method.assert_not_called()


def test_read_agent(agent_name, agent_mail, agent_service):
    #   given
    account = get_account(agent_service)
    agent = asyncio.run(agent_service.create(agent_name, agent_mail, account.id))

    #   when
    result = asyncio.run(agent_service.get(agent.id))

    #   then
    assert agent_name == result.name
    assert agent_mail == result.email
    assert account.id == result.account_id
    assert result.blocked is False


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_remove_agent(mocked_method, agent_name, agent_mail, agent_service):
    #   given
    account = get_account(agent_service)
    agent = asyncio.run(agent_service.create(agent_name, agent_mail, account.id))

    #   when
    asyncio.run(agent_service.delete(account.id, agent.id))

    #   then
    mocked_method.assert_called_with(ANY, region=account.region, agent_uuid=agent.id)
    assert asyncio.run(agent_service.get(agent.id)) is None


def test_read_agent_not_found(agent_service):
    #   when
    result = asyncio.run(agent_service.get(uuid4()))

    #   then
    assert result is None


def test_read_agents(agent_name, agent_mail, agent_service):
    #   given
    how_many = 20
    account = get_account(agent_service)
    for x in range(how_many):
        asyncio.run(agent_service.create(agent_name, str(x) + agent_mail, account.id))

    #   when
    result = asyncio.run(agent_service.get_all())

    #   then
    assert len(result) == how_many


@mock.patch.object(RabbitProducerStub, 'delete_agent', autospec=True)
def test_try_delete_agent_from_other_account(mocked_method, agent_name, agent_mail, agent_service):
    #   given
    account = get_account(agent_service)
    agent = asyncio.run(agent_service.create(agent_name, agent_mail, account.id))

    #   when
    random_account = uuid4()
    with pytest.raises(InconsistencyException):
        asyncio.run(agent_service.delete(random_account, agent.id))

    #   then
    mocked_method.assert_not_called()
