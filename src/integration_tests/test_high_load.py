import asyncio

from integration_tests.populate_the_data import flow_of_the_account
from integration_tests.test_flows import create_accounts, remove_all_accounts

from integration_tests.utils import RestClient
from integration_tests.env import TOKEN, URL


async def _test_create_and_remove_accounts(rest: RestClient):
    # given
    how_many = 100

    # when & then
    await create_accounts(rest, how_many)
    await remove_all_accounts(rest)


async def _test_create_account_with_agents(rest: RestClient):
    # given
    how_many_accounts = 10
    how_many_agents_per_account = 300

    # when
    tasks = []
    for _ in range(0, how_many_accounts):
        tasks.append(asyncio.create_task(flow_of_the_account(rest, how_many_agents_per_account)))
    await asyncio.gather(*tasks)

    # then
    assert how_many_accounts * how_many_agents_per_account == await rest.get_all_agents()


def test_create_and_remove_accounts():
    rest = RestClient(api_token=TOKEN, api_url=URL)

    try:
        asyncio.run(_test_create_and_remove_accounts(rest))
    finally:
        asyncio.run(remove_all_accounts(rest))


def test_create_account_with_agents():
    rest = RestClient(api_token=TOKEN, api_url=URL)

    try:
        asyncio.run(_test_create_account_with_agents(rest))
    finally:
        asyncio.run(remove_all_accounts(rest))
