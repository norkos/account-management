import asyncio

from integration_tests.test_flows import clear_db
from integration_tests.utils import RestClient, generate_account_details, generate_agent_details
from integration_tests.env import TOKEN, URL, TWO_FA


async def flow_of_the_account(api: RestClient, amount_of_agents: int) -> None:
    account_name, email = generate_account_details()
    account_uuid = await api.create_account(account_name, email)

    for agent_number in range(amount_of_agents):
        agent_name, agent_email = generate_agent_details()
        await api.create_agent(account_uuid, agent_name, str(agent_number) + agent_email)


async def async_test_traffic_model(how_many_accounts: int, how_many_agents_per_account: int):
    #   given
    rest = RestClient(api_token=TOKEN, api_url=URL)

    # when
    for _ in range(0, how_many_accounts):
        await flow_of_the_account(rest, how_many_agents_per_account)


def test_populate_low_amount_of_the_data():
    how_many_accounts = 5
    how_many_agents_per_account = 2
    asyncio.run(async_test_traffic_model(how_many_accounts, how_many_agents_per_account))


def test_populate_big_data():
    how_many_accounts = 20
    how_many_agents_per_account = 300
    asyncio.run(async_test_traffic_model(how_many_accounts, how_many_agents_per_account))


def test_drop_the_data():
    rest = RestClient(api_token=TOKEN, api_url=URL, two_fa=TWO_FA)
    asyncio.run(clear_db(rest))
