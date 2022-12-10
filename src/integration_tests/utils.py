import json
import random

import aiohttp
import namegenerator
import names

HTTP_RESPONSE_ACCEPT = {200, 202}


def generate_account_details() -> (str, str):
    account_name_raw = namegenerator.gen()
    account_name = account_name_raw.replace('-', ' ')
    email = f'{account_name_raw}@gmail.com'
    return account_name, email


def generate_agent_details() -> (str, str):
    agent_name = names.get_first_name() + ' ' + names.get_last_name()
    agent_email = f'{agent_name.replace(" ", ".")}@{namegenerator.gen()}.com'
    return agent_name, agent_email


class RestClient:

    def __init__(self, api_token: str, api_url: str):
        self._url = api_url
        self._token = api_token

    async def get_account(self, account_uuid: str) -> {}:
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token}) as session:
            response = await session.get(f'{self._url}/accounts/{account_uuid}')
            return await response.json()

    async def get_agent(self, account: str, agent: str):
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token}) as session:
            response = await session.get(f'{self._url}/accounts/{account}/agents/{agent}')
            return await response.json()

    async def get_agents(self, account: str):
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token}) as session:
            response = await session.get(f'{self._url}/accounts/{account}/agents')
            return (await response.json())['items']

    async def get_amount_of_agents(self, account: str):
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token}) as session:
            response = await session.get(f'{self._url}/accounts/{account}/agents')
            return (await response.json())['total']

    async def get_all_agents(self):
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token}) as session:
            response = await session.get(f'{self._url}/agents')
            return (await response.json())['total']

    async def get_accounts(self) -> {}:
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token}) as session:
            response = await session.get(f'{self._url}/accounts')
            return (await response.json())['items']

    async def create_account(self, name: str, email: str, region: str = None) -> str | None:
        regions = ['nam', 'emea', 'apac']
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token,
                                          'accept': 'application/json',
                                          'Content-Type': 'application/json'
                                          }) as session:
            response = await session.post(f'{self._url}/accounts', data=json.dumps({
                'name': name,
                'email': email,
                'region': region if region else random.choice(regions)}))

            response_status_code = response.status.real

            if response_status_code in HTTP_RESPONSE_ACCEPT:
                content = await response.json()
                account_uuid = content['id']
                print(f'Account {account_uuid} created')
                return account_uuid

            print(f'Cannot create the account for name={name} and mail={email}. '
                  f'Response code={response_status_code}.')
            return None

    async def create_agent(self, account_id: str, name: str, email: str) -> str | None:
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token,
                                          'accept': 'application/json',
                                          'Content-Type': 'application/json'
                                          }) as session:
            response = await session.post(f'{self._url}/accounts/{account_id}/agents',
                                          data=json.dumps({'name': name, 'email': email}))

            response_status_code = response.status.real

            if response_status_code in HTTP_RESPONSE_ACCEPT:
                content = await response.json()
                agent_uuid = content['id']
                print(f'Agent {agent_uuid} created')
                return agent_uuid

            print(f'Cannot create the agent for name={name} and mail={email} for account={account_id}. '
                  f'Response code={response_status_code}.')
            return None

    async def delete_account(self, account_uuid: str) -> None:
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token,
                                          'accept': 'application/json',
                                          }, ) as session:
            result = await session.delete(f'{self._url}/accounts/{account_uuid}')

            if result.status.real in HTTP_RESPONSE_ACCEPT:
                print(f'Account {account_uuid} deleted')
            else:
                print(f'Account {account_uuid} NOT deleted')

    async def block_agent(self, agent_uuid: str) -> bool:
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token,
                                          'accept': 'application/json',
                                          'Content-Type': 'application/json'
                                          }) as session:
            response = await session.post(f'{self._url}/agents/block_agent/{agent_uuid}')
            return response.status.real in HTTP_RESPONSE_ACCEPT

    async def unblock_agent(self, agent_uuid: str) -> bool:
        async with aiohttp.ClientSession(headers=
                                         {'x-token': self._token,
                                          'accept': 'application/json',
                                          'Content-Type': 'application/json'
                                          }) as session:
            response = await session.post(f'{self._url}/agents/unblock_agent/{agent_uuid}')
            return response.status.real in HTTP_RESPONSE_ACCEPT
