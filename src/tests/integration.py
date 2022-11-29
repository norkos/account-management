import aiohttp
import asyncio
import platform
import json
import random
import os
import names

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


TOKEN = os.environ.get('AUTH_TOKEN', 'local')
URL = os.environ.get('URL', 'http://localhost:8080')

HTTP_RESPONSE_ACCEPT = {200, 202}


def rand() -> int:
    return random.randint(0, 2)


async def get_account(uuid: str) -> {}:
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN}) as session:
        response = await session.get(f'{URL}/accounts/{uuid}')
        return await response.json()


async def get_agent(account: str, agent: str):
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN}) as session:
        response = await session.get(f'{URL}/accounts/{account}/agents/{agent}')
        return await response.json()


async def get_agents(account: str):
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN}) as session:
        response = await session.get(f'{URL}/accounts/{account}/agents')
        return await response.json()


async def get_accounts() -> {}:
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN}) as session:
        response = await session.get(f'{URL}/accounts')
        return await response.json()


async def create_account(name: str, email: str) -> str | None:
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN,
                                      'accept': 'application/json',
                                      'Content-Type': 'application/json'
                                      }) as session:
        response = await session.post(f'{URL}/accounts', data=json.dumps({"name": name, "email": email}))

        response_status_code = response.status.real

        if response_status_code in HTTP_RESPONSE_ACCEPT:
            content = await response.json()
            uuid = content['id']
            print(f'Account {uuid} created')
            return uuid

        print(f'Cannot create the account for name={name} and mail={email}. '
              f'Response code={response_status_code}.')
        return None


async def create_agent(account_id: str, name: str, email: str) -> str | None:
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN,
                                      'accept': 'application/json',
                                      'Content-Type': 'application/json'
                                      }) as session:
        response = await session.post(f'{URL}/accounts/{account_id}/agents',
                                      data=json.dumps({"name": name, "email": email}))

        response_status_code = response.status.real

        if response_status_code in HTTP_RESPONSE_ACCEPT:
            content = await response.json()
            uuid = content['id']
            print(f'Agent {uuid} created')
            return uuid

        print(f'Cannot create the agent for name={name} and mail={email}. '
              f'Response code={response_status_code}.')
        return None


async def delete_account(uuid: str) -> None:
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN,
                                      'accept': 'application/json',
                                      }, ) as session:
        result = await session.delete(f'{URL}/accounts/{uuid}')

        if result.status.real in HTTP_RESPONSE_ACCEPT:
            print(f'Account {uuid} deleted')
        else:
            print(f'Account {uuid} NOT deleted')


async def delete_accounts(accounts: {}) -> None:
    if len(accounts) == 0:
        return None

    tasks = []
    for account in accounts:
        tasks.append(asyncio.create_task(delete_account(account['id'])))
    await asyncio.wait(tasks)


async def flow_of_the_account(amount_of_agents: int, delete: bool = True) -> None:
    account_name = names.get_first_name() + '.' + names.get_last_name()
    email = f'{account_name}@gmail.com'

    uuid = await create_account(account_name, email)

    account = await get_account(uuid)

    assert account['name'] == account_name
    assert account['email'] == email

    agents = []
    for x in range(amount_of_agents):
        agent_name = names.get_first_name() + '.' + names.get_last_name()
        agent_email = f'{agent_name}@gmail.com'
        agent = await create_agent(uuid, agent_name, agent_email)
        agents.append(agent)

    response = await get_agents(uuid)
    assert len(response) == amount_of_agents

    if delete:
        await delete_account(account['id'])

        account = await get_account(account['id'])
        assert account['detail'] == 'Account not found'

        for agent in agents:
            response = await get_agent(account, agent)
            assert response['detail'] == 'Agent not found'


async def async_test_traffic_model():
    #   given
    clean_your_data = False
    how_many_accounts = 10
    how_many_agents_per_account = 10

    # when
    tasks = []
    for x in range(0, how_many_accounts):
        tasks.append(asyncio.create_task(flow_of_the_account(how_many_agents_per_account, clean_your_data)))
    await asyncio.gather(*tasks)

    # then
    if clean_your_data:
        accounts = await get_accounts()
        assert len(accounts) == 0


def test_traffic_model():
    asyncio.run(async_test_traffic_model())


async def remove_all_accounts() -> None:
    accounts = await get_accounts()
    print(f'Removing {len(accounts)} accounts.')
    await delete_accounts(accounts)
    accounts = await get_accounts()
    assert len(accounts) == 0


async def create_several_accounts(how_many_accounts: int) -> None:
    tasks = []
    for x in range(0, how_many_accounts):
        name = f'user_name_{x}'
        email = f'test_{x}@google.com'
        tasks.append(asyncio.create_task(create_account(name, email)))

    result = await asyncio.gather(*tasks)
    assert len(result) == how_many_accounts


def test_create_and_remove_accounts():
    # given
    how_many = 100

    # when & then
    asyncio.run(create_several_accounts(how_many))
    asyncio.run(remove_all_accounts())
