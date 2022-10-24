import aio_pika
import os
import asyncio


CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', '')


class Consumer:
    def __init__(self):
        self._accounts = []
        self._connection = None

    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            print(message.body)
            self._accounts.append(message.body)
            await asyncio.sleep(1)

    async def wait_for_rabbit(self, loop, connection_timeout: int) -> None:
        while True:
            try:
                connection = await aio_pika.connect_robust(CLOUDAMQP_URL, loop=loop)
                await connection.close()
                print('RabbitMq is alive !')
                return
            except Exception as error:
                print(f'Waiting for RabbitMQ to be alive. Sleeping {connection_timeout} seconds before retry.')
                await asyncio.sleep(connection_timeout)

    async def consume(self, loop, queue_name: str) -> None:
        self._connection = await aio_pika.connect_robust(CLOUDAMQP_URL, loop=loop)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.consume(self.process_message)

    def accounts(self):
        return self._accounts

    async def close(self):
        if self._connection:
            await self._connection.close()
