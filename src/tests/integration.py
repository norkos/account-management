from uuid import uuid4

import aiohttp
import asyncio
import platform
import json
import random
import os
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


TOKEN = os.environ.get('TOKEN', 'local')
URL = os.environ.get('URL', 'http://localhost:8080')

HTTP_RESPONSE_ACCEPT = {200, 202}


def rand() -> int:
    return random.randint(0, 10)


async def get_account(uuid: str) -> {}:
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN}) as session:
        response = await session.get(f'{URL}/accounts/{uuid}')
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


async def flow_of_the_account() -> None:
    name = str(uuid4())
    email = f'{name}@gmail.com'

    await asyncio.sleep(rand())
    uuid = await create_account(name, email)

    await asyncio.sleep(rand())
    account = await get_account(uuid)

    assert account['name'] == name
    assert account['email'] == email

    await asyncio.sleep(rand())
    await delete_account(account['id'])

    await asyncio.sleep(rand())
    account = await get_account(account['id'])
    assert account['detail'] == 'Account not found'


async def traffic_model(tasks_amount: int) -> None:
    tasks = []

    for x in range(0, tasks_amount):
        tasks.append(asyncio.create_task(flow_of_the_account()))

    await asyncio.gather(*tasks)
    accounts = await get_accounts()
    assert len(accounts) == 0


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


def test_traffic_model():
    how_many = 10
    asyncio.run(traffic_model(how_many))


def test_create_and_remove():
    how_many = 10
    asyncio.run(create_several_accounts(how_many))
    asyncio.run(remove_all_accounts())
