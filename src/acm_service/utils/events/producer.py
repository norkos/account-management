import asyncio
from aio_pika import ExchangeType, Message, DeliveryMode, connect

from acm_service.utils.logconf import DEFAULT_LOGGER

import logging

logger = logging.getLogger(DEFAULT_LOGGER)


def decorate_event(coro):
    async def wrapper(*args, **kwargs):
        retries = 3
        time_out = 1
        retry = 0
        ex = None
        while retry < retries:
            try:
                return await coro(*args, **kwargs)
            except BaseException as e:
                ex = e
                retry += 1
                logger.warning(f'Sending event failed. Retrying for the {retry}. time in {retry * time_out} seconds')
                await asyncio.sleep(retry * time_out)
        logger.exception('Event was not sent. Exception %s', ex)
        raise Exception('Event was not sent')

    return wrapper


class RabbitProducer:

    def __init__(self, url: str):
        self._url = url

    async def _send_customer_event(self, entity_uuid: str, routing_key: str) -> None:
        exchange_name = 'topic_customers'

        connection = await connect(self._url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
            message = Message(entity_uuid.encode('utf-8'), delivery_mode=DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f'Sending the event with body={entity_uuid} to routing key={routing_key}')

    @decorate_event
    async def block_agent(self, region: str, agent_uuid: str) -> None:
        routing_key = f'block.agent.{region}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def unblock_agent(self, region: str, agent_uuid: str) -> None:
        routing_key = f'unblock.agent.{region}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def create_agent(self, region: str, agent_uuid: str) -> None:
        routing_key = f'create.agent.{region}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def delete_agent(self, region: str, agent_uuid: str) -> None:
        routing_key = f'delete.agent.{region}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def create_account(self, region: str, account_uuid: str) -> None:
        routing_key = f'create.account.{region}'
        return await self._send_customer_event(account_uuid, routing_key)

    @decorate_event
    async def delete_account(self, region: str, account_uuid: str) -> None:
        routing_key = f'delete.account.{region}'
        return await self._send_customer_event(account_uuid, routing_key)


class LocalRabbitProducer(RabbitProducer):

    def __init__(self):
        super().__init__('')

    async def _send_customer_event(self, entity_uuid: str, routing_key: str) -> None:
        logger.info(f'Stubbed. Sending the event with body={entity_uuid} to routing key={routing_key}')
