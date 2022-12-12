import asyncio
import platform
import uvicorn
import os

from aio_pika import ExchangeType, Message, DeliveryMode, connect
from fastapi import FastAPI, status, Depends, Header, HTTPException

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

PORT = os.environ.get('PORT', '8070')
API_TOKEN = os.environ.get('AUTH_TOKEN', '')

app = FastAPI(
    title='compliance-service',
    version='1.0',
    docs_url='/_swagger'
)


class RabbitProducer:

    def __init__(self, url: str):
        self._url = url

    async def _send_event(self, entity_uuid: str, routing_key: str) -> None:
        exchange_name = 'topic_compliance'

        connection = await connect(self._url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
            message = Message(entity_uuid.encode('utf-8'), delivery_mode=DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)
            print(f'Sending the event with body={entity_uuid} to routing key={routing_key}')

    async def block_agent(self, agent_uuid: str) -> None:
        routing_key = f'block.agent'
        return await self._send_event(agent_uuid, routing_key)

    async def unblock_agent(self, agent_uuid: str) -> None:
        routing_key = f'unblock.agent'
        return await self._send_event(agent_uuid, routing_key)


event_producer = RabbitProducer(os.environ.get('CLOUDAMQP_URL'))


def get_token_header(x_token: str = Header()) -> bool:
    if x_token != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Token header")
    return True


@app.get("/")
async def root():
    return {'msg': 'Hello my compliance ;) friend !'}


@app.post('/block_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def block_agent(agent_id: str, _auth: bool = Depends(get_token_header)):
    await event_producer.block_agent(agent_id)


@app.post('/unblock_agent/{agent_id}', status_code=status.HTTP_202_ACCEPTED)
async def unblock_agent(agent_id: str, _auth: bool = Depends(get_token_header)):
    await event_producer.unblock_agent(agent_id)


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(PORT),
        workers=1
    )
