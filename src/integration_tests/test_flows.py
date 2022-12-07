import asyncio

from integration_tests.utils import RestClient, generate_account_details, generate_agent_details
from integration_tests.env import TOKEN, URL


async def remove_all_accounts(api: RestClient) -> None:
    accounts = await api.get_accounts()

    if len(accounts) == 0:
        return

    tasks = []
    for account in accounts:
        tasks.append(asyncio.create_task(api.delete_account(account['id'])))
    await asyncio.wait(tasks)

    accounts = await api.get_accounts()
    assert len(accounts) == 0


async def create_accounts(api: RestClient, how_many_accounts: int) -> None:
    tasks = []
    for x in range(0, how_many_accounts):
        name, email = generate_account_details()
        tasks.append(asyncio.create_task(api.create_account(name, email)))

    result = await asyncio.gather(*tasks)
    assert len(result) == how_many_accounts


async def flow_of_the_account(api: RestClient, amount_of_agents: int) -> None:
    account_name, email = generate_account_details()
    account_uuid = await api.create_account(account_name, email)

    #   verify created account
    account = await api.get_account(account_uuid)
    assert account['name'] == account_name
    assert account['email'] == email
    assert account['id'] == account_uuid

    #   create agents
    agents = []
    for x in range(amount_of_agents):
        agent_name, agent_email = generate_agent_details()
        agent_uuid = await api.create_agent(account_uuid, agent_name, agent_email)
        agents.append(agent_uuid)

    #   check if all agents were created
    assert await api.get_amount_of_agents(account_uuid) == amount_of_agents

    #   delete account
    await api.delete_account(account_uuid)

    #   verify that account was deleted
    account = await api.get_account(account_uuid)
    assert 'not found' in account['detail']

    #   verify that agents were deleted
    for agent_uuid in agents:
        response = await api.get_agent(account_uuid, agent_uuid)
        assert 'not found' in response['detail']


async def _test_create_account_with_agents(api: RestClient, how_many_accounts: int, how_many_agents_per_account: int):
    tasks = []
    for x in range(0, how_many_accounts):
        tasks.append(asyncio.create_task(flow_of_the_account(api, how_many_agents_per_account)))
    await asyncio.gather(*tasks)


async def _test_block_and_unblock_agent(api: RestClient) -> None:
    account_name, account_email = generate_account_details()
    account_uuid = await api.create_account(account_name, account_email)

    agent_name, agent_email = generate_agent_details()
    agent_uuid = await api.create_agent(account_uuid, agent_name, agent_email)

    # when
    await api.block_agent(agent_uuid)

    # then
    agent = await api.get_agent(account_uuid, agent_uuid)
    assert agent['blocked']

    # when
    await api.unblock_agent(agent_uuid)

    # then
    agent = await api.get_agent(account_uuid, agent_uuid)
    assert not agent['blocked']


def test_block_and_unblock_agent():
    # given
    rest = RestClient(api_token=TOKEN, api_url=URL)

    try:
        asyncio.run(_test_block_and_unblock_agent(rest))
    finally:
        asyncio.run(remove_all_accounts(rest))


def test_create_and_remove_accounts():
    # given
    how_many_accounts = 10
    rest = RestClient(api_token=TOKEN, api_url=URL)

    try:
        asyncio.run(create_accounts(rest, how_many_accounts))
        asyncio.run(remove_all_accounts(rest))
    finally:
        asyncio.run(remove_all_accounts(rest))


def test_create_account_with_agents():
    # given
    rest = RestClient(api_token=TOKEN, api_url=URL)
    how_many_accounts = 5
    how_many_agents_per_account = 10

    try:
        asyncio.run(_test_create_account_with_agents(rest, how_many_accounts, how_many_agents_per_account))
    finally:
        asyncio.run(remove_all_accounts(rest))
