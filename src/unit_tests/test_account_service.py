import asyncio
import uuid
from unittest.mock import ANY

import mock
import namegenerator
import pytest
from pydantic import ValidationError
from acm_service.data_base.schemas import RegionEnum
from acm_service.services.account_service import AccountService
from acm_service.services.utils import DuplicatedMailException, InconsistencyException

from unit_tests.utils import RabbitProducerStub, AgentRepositoryStub, AccountRepositoryStub


@pytest.fixture
def account_service() -> AccountService:
    return AccountService(AgentRepositoryStub(), AccountRepositoryStub(), RabbitProducerStub())


@pytest.fixture
def account_name() -> str:
    return namegenerator.gen()


@pytest.fixture
def account_email() -> str:
    return f'{namegenerator.gen()}@gmail.com'


@mock.patch.object(RabbitProducerStub, 'create_account', autospec=True)
def test_create_account(mocked_method, account_name, account_email, account_service):
    #   given
    region = RegionEnum.emea
    vip = False

    #   when
    result = asyncio.run(account_service.create_account(account_name, account_email, region, vip))

    #   then
    mocked_method.assert_called_once_with(ANY, region=region, account_uuid=result.id, vip=vip)
    assert account_name == result.name
    assert account_email == result.email
    assert region == result.region
    assert vip == result.vip


def test_create_account_duplicated_mail(account_name, account_email, account_service):
    #   given
    region = RegionEnum.emea
    vip = False
    asyncio.run(account_service.create_account(account_name, account_email, region, vip))

    #   when && then
    with pytest.raises(DuplicatedMailException):
        asyncio.run(account_service.create_account(account_name + account_name, account_email, region, vip))


def test_create_account_invalid_email(account_name, account_email, account_service):
    #   given
    region = RegionEnum.emea
    vip = False

    #   when && then
    with pytest.raises(ValidationError):
        asyncio.run(account_service.create_account(account_name, 'account_email', region, vip))


def test_read_account(account_name, account_email, account_service):
    #   given
    region = RegionEnum.emea
    vip = False
    created = asyncio.run(account_service.create_account(account_name, account_email, region, vip))

    #   when
    result = asyncio.run(account_service.get(created.id))

    #   then
    assert account_name == result.name
    assert account_email == result.email
    assert region == result.region
    assert vip == result.vip


@mock.patch.object(RabbitProducerStub, 'delete_account', autospec=True)
def test_delete_account(mocked_method, account_name, account_email, account_service):
    #   given
    region = RegionEnum.emea
    vip = True
    created = asyncio.run(account_service.create_account(account_name, account_email, region, vip))

    #   when
    asyncio.run(account_service.delete(created.id))

    #   then
    mocked_method.assert_called_with(ANY, region=region, account_uuid=created.id, vip=vip)
    assert asyncio.run(account_service.get(created.id)) is None


def test_delete_not_existing_account(account_service):
    #   given
    random_account = uuid.uuid4()

    #   when && then
    with pytest.raises(InconsistencyException):
        asyncio.run(account_service.delete(random_account))


def test_read_accounts(account_name, account_email, account_service):
    #   given
    region = RegionEnum.emea
    vip = True
    how_many = 20
    for x in range(how_many):
        asyncio.run(account_service.create_account(account_name, str(x) + account_email, region, vip))

    #   when
    result = asyncio.run(account_service.get_all())

    #   then
    assert how_many == len(result)
