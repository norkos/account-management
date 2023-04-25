import asyncio

import pytest

from acm_service.accounts.schema import RegionEnum
from integration_tests.consumer import Consumer
from integration_tests.producer import Producer
from integration_tests.utils import RestClient, generate_account_details, generate_agent_details
from integration_tests.env import TOKEN, URL, RABBIT_MQ, TWO_FA, REDIS_CACHE_INVALIDATION_IN_SECONDS


async def clear_db(api: RestClient) -> None:
    await api.clear_accounts()
    accounts = await api.get_accounts()
    assert len(accounts) == 0


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
    for _ in range(0, how_many_accounts):
        name, email = generate_account_details()
        tasks.append(asyncio.create_task(api.create_account(name, email)))

    result = await asyncio.gather(*tasks)
    assert len(result) == how_many_accounts


async def time_for_lost_events():
    await asyncio.sleep(0.5)


class ProducerWrapper:

    def __init__(self):
        self._producer = Producer(url=RABBIT_MQ)

    async def unblock_agent(self, agent_uuid):
        await self._producer.unblock_agent(agent_uuid)

    async def block_agent(self, agent_uuid):
        await self._producer.block_agent(agent_uuid)


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
        await self._consumer.consume_create_vip_account(loop)
        await self._consumer.consume_delete_vip_account(loop)

    def clean_resources(self):
        self._consumer.created_accounts.clear()
        self._consumer.deleted_accounts.clear()
        self._consumer.created_vip_accounts.clear()
        self._consumer.deleted_vip_accounts.clear()

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

    async def assert_deleted_vip_accounts(self, accounts):
        await time_for_lost_events()
        assert set(accounts) == set(self._consumer.deleted_vip_accounts)

    async def assert_created_vip_accounts(self, accounts):
        await time_for_lost_events()
        assert set(accounts) == set(self._consumer.created_vip_accounts)


class ConsumerEventHandler:
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


class ProducerEventHandler:
    def __init__(self):
        self._producer = None

    async def __aenter__(self) -> ProducerWrapper:
        self._producer = ProducerWrapper()
        return self._producer

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        pass


async def _account_cache(api: RestClient):
    #   create account
    account_name, email = generate_account_details()
    account_uuid = await api.create_account(account_name, email)

    #   cache it
    await api.get_account(account_uuid)

    #   delete account
    await api.delete_account(account_uuid)

    #   read before cache is refreshed
    account = await api.get_account(account_uuid)
    assert account['id'] == account_uuid


async def _agent_cache(api: RestClient):
    #   create account
    account_name, email = generate_account_details()
    account_uuid = await api.create_account(account_name, email)

    #   create agent
    agent_name, agent_email = generate_agent_details()
    agent_uuid = await api.create_agent(account_uuid, agent_name, agent_email)

    #   cache it
    await api.get_agent(account_uuid, agent_uuid)

    #   delete agent
    await api.delete_agent(account_uuid, agent_uuid)

    #   read before cache is refreshed
    agent = await api.get_agent(account_uuid, agent_uuid)
    assert agent['id'] == agent_uuid

    #   wait for the cache to be cleared
    await asyncio.sleep(REDIS_CACHE_INVALIDATION_IN_SECONDS)

    response = await api.get_agent(account_uuid, agent_uuid)
    assert 'not found' in response['detail']


async def flow_of_the_account(api: RestClient, amount_of_agents: int, region: str, vip: bool) -> None:
    async with ConsumerEventHandler(region) as consumer:
        account_name, email = generate_account_details()
        account_uuid = await api.create_account(account_name, email, region, vip)

        #   verify created account
        account = await api.get_account(account_uuid)
        assert account['name'] == account_name
        assert account['email'] == email
        assert account['id'] == account_uuid
        assert account['vip'] == vip
        await consumer.assert_created_accounts([account_uuid])
        if vip:
            await consumer.assert_created_vip_accounts([account_uuid])

        #   create agents
        agents = []
        for _ in range(amount_of_agents):
            agent_name, agent_email = generate_agent_details()
            agent_uuid = await api.create_agent(account_uuid, agent_name, agent_email)
            agents.append(agent_uuid)

        #   check if all agents were created
        assert await api.get_amount_of_agents(account_uuid) == amount_of_agents
        await consumer.assert_created_agents(agents)

        #   delete account
        await api.delete_account(account_uuid)
        await consumer.assert_deleted_accounts([account_uuid])
        if vip:
            await consumer.assert_deleted_vip_accounts([account_uuid])

        #   wait for the cache to be cleared
        await asyncio.sleep(REDIS_CACHE_INVALIDATION_IN_SECONDS)

        #   verify that account was deleted
        account = await api.get_account(account_uuid)
        assert 'not found' in account['detail']

        #   verify that agents were deleted
        for agent_uuid in agents:
            response = await api.get_agent(account_uuid, agent_uuid)
            assert 'not found' in response['detail']
        await consumer.assert_deleted_agents(agents)


async def _test_block_and_unblock_agent_via_event(api: RestClient, region: str) -> None:
    async with ConsumerEventHandler(region) as consumer:
        async with ProducerEventHandler() as producer:
            return await _test_block_and_unblock_agent(api, region, consumer, producer)


async def _test_block_and_unblock_agent_via_rest(api: RestClient, region: str) -> None:
    async with ConsumerEventHandler(region) as consumer:
        return await _test_block_and_unblock_agent(api, region, consumer, api)


async def _test_block_and_unblock_agent(api: RestClient, region: str,
                                        consumer: ConsumerWrapper, someone_to_block) -> None:
    account_name, account_email = generate_account_details()
    account_uuid = await api.create_account(account_name, account_email, region)

    agent_name, agent_email = generate_agent_details()
    agent_uuid = await api.create_agent(account_uuid, agent_name, agent_email)

    # when
    await someone_to_block.block_agent(agent_uuid)

    #   wait for the cache to be cleared
    await asyncio.sleep(REDIS_CACHE_INVALIDATION_IN_SECONDS)

    # then
    agent = await api.get_agent(account_uuid, agent_uuid)
    assert agent['blocked']
    await consumer.assert_blocked_agents([agent_uuid])

    # when
    await someone_to_block.unblock_agent(agent_uuid)

    #   wait for the cache to be cleared
    await asyncio.sleep(REDIS_CACHE_INVALIDATION_IN_SECONDS)

    # then
    agent = await api.get_agent(account_uuid, agent_uuid)
    assert not agent['blocked']
    await consumer.assert_blocked_agents([])


@pytest.fixture
def rest() -> RestClient:
    return RestClient(api_token=TOKEN, api_url=URL, two_fa=TWO_FA)


@pytest.fixture(autouse=True)
def fixture_func(tmpdir):
    yield
    asyncio.run(clear_db(RestClient(api_token=TOKEN, api_url=URL, two_fa=TWO_FA)))


def test_block_and_unblock_agent_via_rest(rest):
    # given
    region = RegionEnum.apac
    asyncio.run(_test_block_and_unblock_agent_via_rest(rest, region.value))


def test_block_and_unblock_agent_via_events(rest):
    # given
    region = RegionEnum.nam
    asyncio.run(_test_block_and_unblock_agent_via_event(rest, region.value))


def test_create_account_with_agents(rest):
    # given
    how_many_agents = 5
    region = RegionEnum.emea

    asyncio.run(flow_of_the_account(rest, how_many_agents, region.value, vip=True))
    asyncio.run(flow_of_the_account(rest, how_many_agents, region.value, vip=False))


def test_create_and_remove_accounts(rest):
    # given
    how_many_accounts = 5
    asyncio.run(create_accounts(rest, how_many_accounts))
    asyncio.run(remove_all_accounts(rest))


def test_account_cache(rest):
    asyncio.run(_account_cache(rest))


def test_agent_cache(rest):
    asyncio.run(_agent_cache(rest))
