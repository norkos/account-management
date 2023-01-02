import uuid
from unittest.mock import ANY
from uuid import uuid4

import mock
import pytest
from requests import Response

from acm_service.utils.env import AUTH_TOKEN, TWO_FA
from data_base.schemas import RegionEnum

from unit_tests.utils import RabbitProducerStub, generate_random_mail
from unit_tests.sut import client, reset_database


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    reset_database()


def create_account(name: str = 'dummy', email: str = None,
                   region: RegionEnum = RegionEnum.nam, vip: bool = False) -> Response:
    return client.post(
        '/accounts',
        headers={'X-Token': AUTH_TOKEN},
        json={'name': name, 'email': email if email is not None else generate_random_mail(),
              'region': region.value, 'vip': str(vip)}
    )


@mock.patch.object(RabbitProducerStub, 'create_account', autospec=True)
def test_create_account(mocked_method):
    name = 'my_name'
    mail = generate_random_mail()
    region = RegionEnum.emea
    vip = True

    response = create_account(name, mail, region, vip)
    mocked_method.assert_called_once_with(ANY, region=region, account_uuid=uuid.UUID(response.json()['id']), vip=vip)

    assert response.status_code == 200
    assert response.json()['name'] == name
    assert response.json()['email'] == mail
    assert response.json()['region'] == region
    assert response.json()['vip'] == vip


def test_create_account_duplicated_mail():
    mail = generate_random_mail()
    create_account(email=mail)
    response = create_account(email=mail)

    assert response.status_code == 400
    assert response.json() == {"detail": "E-mail already used"}


def test_create_account_invalid_mail():
    response = create_account('my_name2', 'my_mailman.com')
    assert response.status_code == 422


def test_create_accounts_bad_token():
    mail = generate_random_mail()
    response = client.post(
        '/accounts',
        headers={"X-Token": "wrong one"},
        json={'name': 'my_name', 'email': mail}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_account():
    name = 'my_name'
    mail = generate_random_mail()
    region = RegionEnum.emea
    vip = True
    create_response = create_account(name, mail, region, vip)
    account_id = create_response.json()['id']

    read_response = client.get(
        f'/accounts/{account_id}',
        headers={"X-Token": AUTH_TOKEN}
    )
    assert read_response.status_code == 200
    assert read_response.json() == {
        'id': account_id,
        'name':  name,
        'email': mail,
        'region': region.value,
        'vip': vip
    }


@mock.patch.object(RabbitProducerStub, 'delete_account', autospec=True)
def test_delete_account(mocked_method):
    region = RegionEnum.emea
    vip = False
    create_response = create_account(region=region, vip=vip)

    account_id = create_response.json()["id"]
    delete_response = client.delete(
        f'/accounts/{account_id}',
        headers={"X-Token": AUTH_TOKEN}
    )
    assert delete_response.status_code == 202
    mocked_method.assert_called_with(ANY, region=region,
                                     account_uuid=uuid.UUID(create_response.json()["id"]), vip=vip)

    read_response = client.get(
        f'/accounts/{create_response.json()["id"]}',
        headers={"X-Token": AUTH_TOKEN}
    )
    assert read_response.status_code == 404
    assert read_response.json() == {"detail": f"Account {account_id} not found"}


def test_read_account_bad_token():
    create_response = create_account()

    read_response = client.get(
        f'/accounts/{create_response.json()["id"]}',
        headers={'X-Token': 'wrong one'}
    )

    assert read_response.status_code == 400
    assert read_response.json() == {'detail': 'Invalid X-Token header'}


def test_read_account_not_found():
    random_uuid = uuid4()
    response = client.get(
        f'/accounts/{random_uuid}',
        headers={"X-Token": AUTH_TOKEN}
    )
    assert response.status_code == 404
    assert response.json() == {'detail': f'Account {random_uuid} not found'}


def test_read_accounts():
    how_many = 20
    for _ in range(how_many):
        create_account()

    response = client.get(
        '/accounts?page=1&size=100',
        headers={'X-Token': AUTH_TOKEN}
    )

    assert response.status_code == 200
    assert len(response.json()['items']) == how_many


def test_read_accounts_bad_token():
    response = client.get(
        '/accounts/',
        headers={'X-Token': 'wrong one'}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid X-Token header'}


@mock.patch.object(RabbitProducerStub, 'delete_account', autospec=True)
def test_can_remove_all_accounts(mocked_method):
    create_account()
    create_account()

    response = client.post(
        '/accounts/clear',
        headers={'X-Token': AUTH_TOKEN,
                 'TWO-FA': TWO_FA}
    )
    mocked_method.assert_called_with(ANY, region=None, account_uuid=None, vip=True)

    assert response.status_code == 202


def test_cannot_remove_all_accounts():
    create_account()
    create_account()

    response = client.post(
        '/accounts/clear',
        headers={'X-Token': AUTH_TOKEN}
    )

    assert response.status_code == 422
