from uuid import uuid4

from unittest import mock
from unittest.mock import ANY
from unit_tests.utils import generate_random_mail

import namegenerator
from pydantic import EmailStr
from fastapi.testclient import TestClient

from acm_service.utils.env import AUTH_TOKEN
from acm_service.data_base.schemas import RegionEnum, AccountWithoutAgents
from acm_service.services.account_service import AccountService
from acm_service.services.utils import DuplicatedMailException

from main import app

client = TestClient(app)

simple_account = AccountWithoutAgents(id=uuid4(),
                                      name=namegenerator.gen(),
                                      email=EmailStr(generate_random_mail()),
                                      region=RegionEnum.emea,
                                      vip=True)


@mock.patch.object(AccountService, 'create', return_value=simple_account, autospec=True)
def test_create_account(mocked_method):
    #   given
    name = simple_account.name
    email = simple_account.email
    region = simple_account.region
    vip = simple_account.vip

    #   when
    response = client.post(
        '/accounts',
        headers={'X-Token': AUTH_TOKEN},
        json={'name': name, 'email': email, 'region': region, 'vip': str(vip)}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, name=name, email=email, region=region, vip=vip)
    assert response.status_code == 200
    assert response.json()['name'] == name
    assert response.json()['email'] == email
    assert response.json()['region'] == region
    assert response.json()['vip'] == vip


@mock.patch.object(AccountService, 'create', autospec=True)
def test_create_account_duplicated_mail(mocked_method):
    #   given
    mocked_method.side_effect = DuplicatedMailException()

    #   when
    response = client.post(
        '/accounts',
        headers={'X-Token': AUTH_TOKEN},
        json={'name': simple_account.name, 'email': simple_account.email,
              'region': simple_account.region, 'vip': str(simple_account.vip)}
    )

    #   then
    assert response.status_code == 400
    assert response.json() == {'detail': 'E-mail is already used'}


def test_create_account_invalid_mail():
    #   given
    email = 'invalid'

    #   when
    response = client.post(
        '/accounts',
        headers={'X-Token': AUTH_TOKEN},
        json={'name': simple_account.name, 'email': email,
              'region': simple_account.region, 'vip': str(simple_account.vip)}
    )

    #   then
    assert response.status_code == 422


def test_create_accounts_bad_token():
    #   given
    token = 'wrong one'

    #   when
    response = client.post(
        '/accounts',
        headers={'X-Token': token},
        json={'name': simple_account.name, 'email': simple_account.email}
    )

    #   then
    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid X-Token header'}


@mock.patch.object(AccountService, 'get', return_value=simple_account, autospec=True)
def test_read_account(mocked_method):
    #   given & when
    read_response = client.get(
        f'/accounts/{simple_account.id}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, account_id=simple_account.id)
    assert read_response.status_code == 200
    assert read_response.json() == {
        'id': str(simple_account.id),
        'name': simple_account.name,
        'email': simple_account.email,
        'region': simple_account.region.value,
        'vip': simple_account.vip
    }


def test_read_account_bad_token():
    #   given
    token = 'bad_one'

    #   when
    read_response = client.get(
        f'/accounts/{simple_account.id}',
        headers={'X-Token': token}
    )

    #   then
    assert read_response.status_code == 400
    assert read_response.json() == {'detail': 'Invalid X-Token header'}


@mock.patch.object(AccountService, 'delete', return_value=simple_account, autospec=True)
def test_delete_account(mocked_method):
    #   given & when
    response = client.delete(
        f'/accounts/{simple_account.id}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, account_id=simple_account.id)
    assert response.status_code == 202


@mock.patch.object(AccountService, 'get', return_value=None, autospec=True)
def test_read_account_not_found(mocked_method):
    #   given
    random_uuid = uuid4()

    #   when
    response = client.get(
        f'/accounts/{random_uuid}',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY, account_id=random_uuid)
    assert response.status_code == 404
    assert response.json() == {'detail': f'Account {random_uuid} not found'}


@mock.patch.object(AccountService, 'get_all', return_value=[simple_account, simple_account], autospec=True)
def test_read_accounts(mocked_method):
    #   given & when
    response = client.get(
        '/accounts?page=1&size=100',
        headers={'X-Token': AUTH_TOKEN}
    )

    #   then
    mocked_method.assert_called_once_with(ANY)
    assert response.status_code == 200
    assert len(response.json()['items']) == 2


def test_read_accounts_bad_token():
    #   given
    token = 'wrong_token'

    #   when
    response = client.get(
        '/accounts/',
        headers={'X-Token': token}
    )

    #   then
    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid X-Token header'}
