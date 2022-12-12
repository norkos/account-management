from typing import Callable

import aio_pika
import asyncio

from aio_pika import ExchangeType, connect_robust


def decode(message: aio_pika.abc.AbstractIncomingMessage) -> str:
    return message.body.decode('utf-8')


class Consumer:
    def __init__(self, url: str):
        self._deleted_vip_accounts = []
        self._created_vip_accounts = []
        self._connection = None
        self._url = url

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

    async def create_vip_account(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            print(f'Create vip account: {uuid}')
            self._created_vip_accounts.append(uuid)

    async def delete_vip_account(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            print(f'Delete account: {uuid}')
            self._deleted_vip_accounts.append(uuid)

    # noinspection DuplicatedCode
    async def consume(self, loop, binding_key: str, callback: Callable) -> None:
        queue_name = f'{binding_key}_queue'.replace('*', '_')

        self._connection = await connect_robust(self._url, loop=loop)
        channel = await self._connection.channel()
        exchange = await channel.declare_exchange(name='topic_customers', type=ExchangeType.TOPIC)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=binding_key)
        await queue.consume(callback)

    async def consume_create_vip_account(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'create.account.*.vip', callback=self.create_vip_account)

    async def consume_delete_vip_account(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'delete.account.*.vip', callback=self.delete_vip_account)

    @property
    def created_vip_accounts(self) -> [str]:
        return self._created_vip_accounts

    @property
    def deleted_vip_accounts(self) -> [str]:
        return self._deleted_vip_accounts

    async def close(self):
        if self._connection:
            await self._connection.close()
