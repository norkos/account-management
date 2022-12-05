import asyncio
import json
import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode, connect_robust, connect

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

    @decorate_event
    async def async_publish(self, method, body) -> None:
        connection = await connect_robust(self._url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(body).encode()
                ),
                routing_key='main'
            )
            logger.info(f'Sending the event to queue: {body}')

    @decorate_event
    async def create_agent(self, agent_uuid) -> None:
        routing_key = 'create.agent.emea'
        exchange_name = 'topic_customers'

        connection = await connect(self._url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
            message = Message(json.dumps(agent_uuid).encode(), delivery_mode=DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f'Sending the event with body={agent_uuid} to routing key={routing_key}')

    @decorate_event
    async def delete_agent(self, agent_uuid) -> None:
        routing_key = 'delete.agent.emea'
        exchange_name = 'topic_customers'

        connection = await connect(self._url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
            message = Message(json.dumps(agent_uuid).encode(), delivery_mode=DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f'Sending the event with body={agent_uuid} to routing key={routing_key}')

    @decorate_event
    async def create_account(self, account_uuid):
        routing_key = 'create.account.emea'
        exchange_name = 'topic_customers'

        connection = await connect(self._url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
            message = Message(json.dumps(account_uuid).encode(), delivery_mode=DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f'Sending the event with body={account_uuid} to routing key={routing_key}')

    @decorate_event
    async def delete_account(self, account_uuid):
        routing_key = 'delete.account.emea'
        exchange_name = 'topic_customers'

        connection = await connect(self._url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
            message = Message(json.dumps(account_uuid).encode(), delivery_mode=DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f'Sending the event with body={account_uuid} to routing key={routing_key}')


class LocalRabbitProducer(RabbitProducer):

    def __init__(self):
        super().__init__('')

    async def async_publish(self, method, body) -> None:
        logger.info(f'Sending the event to queue: {body}')
