import json

import aio_pika
import uvicorn
import os
import logging
from fastapi import FastAPI, status


PORT = os.environ.get('PORT', '8070')

app = FastAPI(
    title='compliance-service',
    version='0.1',
    docs_url='/_swagger'
)


class RabbitProducer:

    def __init__(self):
        self._url = os.environ.get('CLOUDAMQP_URL')

    async def block_agent(self, agent_id: str) -> None:
        logging.info(f'Blocking agent: {agent_id}')
        connection = await aio_pika.connect_robust(self._url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(agent_id).encode()
                ),
                routing_key='main'
            )

    async def unblock_agent(self, agent_id: str) -> None:
        logging.info(f'Unblocking agent: {agent_id}')
        connection = await aio_pika.connect_robust(self._url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(agent_id).encode()
                ),
                routing_key='main'
            )


event_producer = RabbitProducer()


@app.get("/")
async def root():
    return {'msg': 'Hello my friend !'}


@app.post('/block_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def block_agent(agent_id: str):
    await event_producer.block_agent(agent_id)


@app.post('/unblock_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def unblock_agent(agent_id: str):
    await event_producer.unblock_agent(agent_id)


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(PORT),
        workers=1
    )
