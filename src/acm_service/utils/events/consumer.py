import aio_pika
import asyncio


class Consumer:
    def __init__(self, url: str):
        self._accounts = []
        self._url = url
        self._connection = None

    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            print(message.body)

    async def wait_for_rabbit(self, loop, connection_timeout: int) -> None:
        while True:
            try:
                connection = await aio_pika.connect_robust(self._url, loop=loop)
                await connection.close()
                print('RabbitMq is alive !')
                return
            except Exception as error:
                print(f'Waiting for RabbitMQ to be alive. Sleeping {connection_timeout} seconds before retry.')
                await asyncio.sleep(connection_timeout)

    async def consume(self, loop, queue_name: str) -> None:
        self._connection = await aio_pika.connect_robust(self._url, loop=loop)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.consume(self.process_message)

    async def close(self):
        if self._connection:
            await self._connection.close()
