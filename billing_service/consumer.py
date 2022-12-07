from typing import Callable

import aio_pika
import os
import asyncio

from aio_pika import ExchangeType, connect_robust


class Consumer:
    def __init__(self, region: str):
        self._blocked_agents = set([])
        self._deleted_accounts = []
        self._created_accounts = []
        self._created_agents = []
        self._deleted_agents = []
        self._region = region
        self._connection = None
        self._url = os.environ.get('CLOUDAMQP_URL', '')

    async def wait_for_rabbit(self, loop, connection_timeout: int) -> None:
        while True:
            try:
                connection = await connect_robust(self._url, loop=loop)
                await connection.close()
                print('RabbitMq is alive !')
                return
            except Exception:
                print(f'Waiting for RabbitMQ to be alive. Sleeping {connection_timeout} seconds before retry.')
                await asyncio.sleep(connection_timeout)

    async def block_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            print(f'Block agent: {message.body}')
            self._blocked_agents.add(message.body)

    async def unblock_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            if message.body in self._blocked_agents:
                print(f'Unblock agent: {message.body}')
                self._blocked_agents.remove(message.body)

    async def create_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            print(f'Create agent: {message.body}')
            self._created_agents.append(message.body)

    async def delete_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            print(f'Delete agent: {message.body}')
            self._deleted_agents.append(message.body)

    async def create_account(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            print(f'Create account: {message.body}')
            self._created_accounts.append(message.body)

    async def delete_account(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            print(f'Delete account: {message.body}')
            self._deleted_accounts.append(message.body)

    async def consume(self, loop, binding_key: str, callback: Callable) -> None:
        queue_name = f'{binding_key}_queue'

        self._connection = await connect_robust(self._url, loop=loop)
        channel = await self._connection.channel()
        exchange = await channel.declare_exchange(name='topic_customers', type=ExchangeType.TOPIC)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=binding_key)
        await queue.consume(callback)

    async def consume_create_agent(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'create.agent.{self._region}', callback=self.create_agent)

    async def consume_delete_agent(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'delete.agent.{self._region}', callback=self.delete_agent)

    async def consume_create_account(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'create.account.{self._region}', callback=self.create_account)

    async def consume_delete_account(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'delete.account.{self._region}', callback=self.delete_account)

    async def consume_block_agent(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'block.agent.{self._region}', callback=self.block_agent)

    async def consume_unblock_agent(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'unblock.agent.{self._region}', callback=self.unblock_agent)

    def created_agents(self) -> [str]:
        return self._created_agents

    def deleted_agents(self) -> [str]:
        return self._deleted_agents
    
    def blocked_agents(self) -> [str]:
        return self._blocked_agents

    def created_accounts(self) -> [str]:
        return self._created_accounts

    def deleted_accounts(self) -> [str]:
        return self._deleted_accounts

    async def close(self):
        if self._connection:
            await self._connection.close()
