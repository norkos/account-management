from uuid import uuid4

import aiohttp
import asyncio
import platform
import json


if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TOKEN = 'local'
URL = 'http://localhost:8080'

HTTP_RESPONSE_ACCEPT = {200, 202}


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


async def flow_of_the_account():
    name = str(uuid4())
    email = f'{name}@gmail.com'

    uuid = await create_account(name, email)
    await asyncio.sleep(0.1)
    account = await get_account(uuid)

    assert account['name'] == name
    assert account['email'] == email
    await asyncio.sleep(0.1)

    await delete_account(account['id'])
    account = await get_account(account['id'])

    await asyncio.sleep(0.1)
    assert account['detail'] == 'Account not found'


async def traffic_model(tasks_amount: int):
    tasks = []

    for x in range(0, tasks_amount):
        tasks.append(asyncio.create_task(flow_of_the_account()))

    await asyncio.gather(*tasks)
    accounts = await get_accounts()
    assert len(accounts) == 0


async def remove_all_accounts():
    accounts = await get_accounts()
    print(f'Removing {len(accounts)} accounts.')
    await delete_accounts(accounts)
    accounts = await get_accounts()
    assert len(accounts) == 0


async def create_several_accounts():
    how_many = 100
    tasks = []
    for x in range(0, how_many):
        name = f'user_name_{x}'
        email = f'test_{x}@google.com'
        tasks.append(asyncio.create_task(create_account(name, email)))

    result = await asyncio.gather(*tasks)
    assert len(result) == how_many


if __name__ == "__main__":
    asyncio.run(create_several_accounts())
    asyncio.run(remove_all_accounts())
    asyncio.run(traffic_model(1))
