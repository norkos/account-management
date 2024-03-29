from typing import Callable
import asyncio

import aio_pika
from aio_pika import ExchangeType, connect_robust


def decode(message: aio_pika.abc.AbstractIncomingMessage) -> str:
    return message.body.decode('utf-8')


class Consumer:
    def __init__(self, region: str, url: str):
        self._blocked_agents = set([])
        self._deleted_accounts = []
        self._created_accounts = []
        self._created_agents = []
        self._deleted_agents = []
        self._region = region
        self._connection = None
        self._url = url

    async def wait_for_rabbit(self, loop, connection_timeout: int) -> None:
        while True:
            try:
                self._connection = await connect_robust(self._url, loop=loop)
                print('RabbitMq is alive !')
                return
            except Exception:
                print(f'Waiting for RabbitMQ to be alive. Sleeping {connection_timeout} seconds before retry.')
                await asyncio.sleep(connection_timeout)

    async def block_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            print(f'Block agent: {uuid}')
            self._blocked_agents.add(uuid)

    async def unblock_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            if uuid in self._blocked_agents:
                print(f'Unblock agent: {uuid}')
                self._blocked_agents.remove(uuid)

    async def create_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            print(f'Create agent: {uuid}')
            self._created_agents.append(uuid)

    async def delete_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            print(f'Delete agent: {uuid}')
            self._deleted_agents.append(uuid)

    async def create_account(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            print(f'Create account: {uuid}')
            self._created_accounts.append(uuid)

    async def delete_account(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            print(f'Delete account: {uuid}')
            self._deleted_accounts.append(uuid)

    # noinspection DuplicatedCode
    async def consume(self, binding_key: str, callback: Callable) -> None:
        queue_name = f'{binding_key}_queue'

        channel = await self._connection.channel()
        exchange = await channel.declare_exchange(name='topic_customers', type=ExchangeType.TOPIC)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=binding_key)
        await queue.consume(callback)

    async def consume_create_agent(self) -> None:
        await self.consume(binding_key=f'create.agent.{self._region}', callback=self.create_agent)

    async def consume_delete_agent(self) -> None:
        await self.consume(binding_key=f'delete.agent.{self._region}', callback=self.delete_agent)

    async def consume_create_account(self) -> None:
        await self.consume(binding_key=f'create.account.{self._region}.#', callback=self.create_account)

    async def consume_delete_account(self) -> None:
        await self.consume(binding_key=f'delete.account.{self._region}.#', callback=self.delete_account)

    async def consume_block_agent(self) -> None:
        await self.consume(binding_key=f'block.agent.{self._region}', callback=self.block_agent)

    async def consume_unblock_agent(self) -> None:
        await self.consume(binding_key=f'unblock.agent.{self._region}', callback=self.unblock_agent)

    @property
    def created_agents(self) -> [str]:
        return self._created_agents

    @property
    def deleted_agents(self) -> [str]:
        return self._deleted_agents

    @property
    def blocked_agents(self) -> [str]:
        return self._blocked_agents

    @property
    def created_accounts(self) -> [str]:
        return self._created_accounts

    @property
    def deleted_accounts(self) -> [str]:
        return self._deleted_accounts

    async def close(self):
        if self._connection:
            await self._connection.close()
