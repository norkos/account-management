import uvicorn
import os
from fastapi import FastAPI
import asyncio
import aio_pika

PORT = os.environ.get('PORT', '8070')
CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', '')

app = FastAPI(
    title='event-consumer',
    version='0.1',
    docs_url='/_swagger'
)

accounts = []


@app.get("/")
async def root():
    return {'Created accounts since I am alive: ': str(accounts)}


async def process_message(message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
    async with message.process():
        print(message.body)
        accounts.append(message.body)
        await asyncio.sleep(1)


async def wait_for_rabbit(loop, connection_timeout: int) -> None:
    while True:
        try:
            connection = await aio_pika.connect_robust(CLOUDAMQP_URL, loop=loop)
            await connection.close()
            print('RabbitMq is alive !')
            return
        except Exception as error:
            print(f'Waiting for RabbitMQ to be alive. Sleeping {connection_timeout} seconds before retry.')
            await asyncio.sleep(connection_timeout)


async def consume(loop, queue_name: str) -> None:
    connection = await aio_pika.connect_robust(CLOUDAMQP_URL, loop=loop)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.consume(process_message)


@app.on_event("startup")
async def startup():
    connection_timeout = 5
    queue_name = 'main'
    loop = asyncio.get_running_loop()
    await wait_for_rabbit(loop, connection_timeout)
    await consume(loop, queue_name)


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(PORT),
        workers=1
    )
