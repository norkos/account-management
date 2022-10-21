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
        content = await response.json()

        response_status_code = response.status.real
        if response_status_code in HTTP_RESPONSE_ACCEPT:
            uuid = content['id']
            print(f'Account {uuid} created')
            return uuid

        print(f'Cannot create the account for name={name} and mail={email}. '
              f'Response code={response_status_code} with msg={content}.')
        return None


async def delete_account(uuid: str) -> None:
    async with aiohttp.ClientSession(headers=
                                     {'x-token': TOKEN,
                                      'accept': 'application/json',
                                      },) as session:
        result = await session.delete(f'{URL}/accounts/{uuid}')

        if result.status.real in HTTP_RESPONSE_ACCEPT:
            print(f'Account {uuid} deleted')
        else:
            print(f'Account {uuid} NOT deleted')


async def delete_accounts(accounts: {}) -> None:
    tasks = []
    for account in accounts:
        tasks.append(asyncio.create_task(delete_account(account['id'])))
    await asyncio.wait(tasks)


if __name__ == "__main__":
    asyncio.run(deleted_accounts())
    asyncio.run(create_account('jan', '121ka@wp.pl'))
    asyncio.run(delete_account('a0ad7f0f-922f-490e-9315-eb1fbeb03adb'))
    print(asyncio.run(get_account('a0ad7f0f-922f-490e-9315-eb1fbeb03adb')))
