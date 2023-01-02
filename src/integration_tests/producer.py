from aio_pika import ExchangeType, Message, DeliveryMode, connect

from acm_service.utils.env import ENCODING


class Producer:

    def __init__(self, url: str):
        self._url = url

    async def _send_event(self, entity_uuid: str, routing_key: str) -> None:
        exchange_name = 'topic_compliance'

        connection = await connect(self._url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
            message = Message(entity_uuid.encode(ENCODING), delivery_mode=DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)

    async def block_agent(self, agent_uuid: str) -> None:
        routing_key = 'block.agent'
        return await self._send_event(agent_uuid, routing_key)

    async def unblock_agent(self, agent_uuid: str) -> None:
        routing_key = 'unblock.agent'
        return await self._send_event(agent_uuid, routing_key)
