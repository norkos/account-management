import asyncio
import sys

from integration_tests.utils import RestClient, generate_account_details, generate_agent_details
from integration_tests.env import TOKEN, URL, RABBIT_MQ

# some magic needed to see billing package without propagating __init__
import pathlib
sys.path.append(str(pathlib.Path().resolve()))
from billing_service.consumer import Consumer


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


async def time_for_lost_events():
    await asyncio.sleep(0.5)


class ConsumerWrapper:

    def __init__(self, region: str):
        self._consumer = Consumer(region, url=RABBIT_MQ)

    async def close(self):
        await self._consumer.close()

    async def consume_events(self, loop):
        await self._consumer.consume_create_account(loop)
        await self._consumer.consume_delete_account(loop)
        await self._consumer.consume_create_agent(loop)
        await self._consumer.consume_delete_agent(loop)
        await self._consumer.consume_block_agent(loop)
        await self._consumer.consume_unblock_agent(loop)

    def clean_resources(self):
        self._consumer.created_accounts.clear()
        self._consumer.deleted_accounts.clear()
        self._consumer.created_agents.clear()
        self._consumer.deleted_agents.clear()
        self._consumer.blocked_agents.clear()

    async def assert_created_accounts(self, accounts):
        await time_for_lost_events()
        assert set(accounts) == set(self._consumer.created_accounts)

    async def assert_deleted_accounts(self, accounts):
        await time_for_lost_events()
        assert set(accounts) == set(self._consumer.deleted_accounts)

    async def assert_created_agents(self, agents):
        await time_for_lost_events()
        assert set(agents) == set(self._consumer.created_agents)

    async def assert_deleted_agents(self, agents):
        await time_for_lost_events()
        assert set(agents) == set(self._consumer.deleted_agents)

    async def assert_blocked_agents(self, agents):
        await time_for_lost_events()
        assert set(agents) == set(self._consumer.blocked_agents)


class EventHandler:
    def __init__(self, region: str):
        self._region = region
        self._consumer = None

    async def __aenter__(self) -> ConsumerWrapper:
        self._consumer = ConsumerWrapper(self._region)
        loop = asyncio.get_running_loop()
        await self._consumer.consume_events(loop)
        await asyncio.sleep(1)  # get time to get everything what was left in queues from some elder runs
        self._consumer.clean_resources()
        return self._consumer

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self._consumer.close()


async def flow_of_the_account(api: RestClient, amount_of_agents: int, region: str) -> None:
    async with EventHandler(region) as consumer:
        account_name, email = generate_account_details()
        account_uuid = await api.create_account(account_name, email, region)

        #   verify created account
        account = await api.get_account(account_uuid)
        assert account['name'] == account_name
        assert account['email'] == email
        assert account['id'] == account_uuid
        await consumer.assert_created_accounts([account_uuid])

        #   create agents
        agents = []
        for x in range(amount_of_agents):
            agent_name, agent_email = generate_agent_details()
            agent_uuid = await api.create_agent(account_uuid, agent_name, agent_email)
            agents.append(agent_uuid)

        #   check if all agents were created
        assert await api.get_amount_of_agents(account_uuid) == amount_of_agents
        await consumer.assert_created_agents(agents)

        #   delete account
        await api.delete_account(account_uuid)
        await consumer.assert_deleted_accounts([account_uuid])

        #   verify that account was deleted
        account = await api.get_account(account_uuid)
        assert 'not found' in account['detail']

        #   verify that agents were deleted
        for agent_uuid in agents:
            response = await api.get_agent(account_uuid, agent_uuid)
            assert 'not found' in response['detail']
        await consumer.assert_deleted_agents(agents)


async def _test_block_and_unblock_agent_via_rest(api: RestClient, region: str) -> None:
    async with EventHandler(region) as consumer:
        account_name, account_email = generate_account_details()
        account_uuid = await api.create_account(account_name, account_email, region)

        agent_name, agent_email = generate_agent_details()
        agent_uuid = await api.create_agent(account_uuid, agent_name, agent_email)

        # when
        await api.block_agent(agent_uuid)

        # then
        agent = await api.get_agent(account_uuid, agent_uuid)
        assert agent['blocked']
        await consumer.assert_blocked_agents([agent_uuid])

        # when
        await api.unblock_agent(agent_uuid)

        # then
        agent = await api.get_agent(account_uuid, agent_uuid)
        assert not agent['blocked']
        await consumer.assert_blocked_agents([])


def test_block_and_unblock_agent_via_rest():
    # given
    rest = RestClient(api_token=TOKEN, api_url=URL)
    region = 'apac'

    try:
        asyncio.run(_test_block_and_unblock_agent_via_rest(rest, region))
    finally:
        asyncio.run(remove_all_accounts(rest))


def test_create_account_with_agents():
    # given
    rest = RestClient(api_token=TOKEN, api_url=URL)
    how_many_agents = 5
    region = 'emea'

    try:
        asyncio.run(flow_of_the_account(rest, how_many_agents, region))
    finally:
        asyncio.run(remove_all_accounts(rest))


def test_create_and_remove_accounts():
    # given
    how_many_accounts = 5
    rest = RestClient(api_token=TOKEN, api_url=URL)

    try:
        asyncio.run(create_accounts(rest, how_many_accounts))
    finally:
        asyncio.run(remove_all_accounts(rest))
