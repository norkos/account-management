import asyncio
import logging

from aio_pika import ExchangeType, Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.env import ENCODING

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
            except BaseException as exc:
                ex = exc
                retry += 1
                logger.warning(f'Sending event failed. Retrying for the {retry}. time in {retry * time_out} seconds')
                await asyncio.sleep(retry * time_out)
        logger.exception('Event was not sent. Exception %s', ex)
        raise Exception('Event was not sent')

    return wrapper


class EventProducer:

    instance = None

    @classmethod
    def get_instance(cls):
        if EventProducer.instance is None:
            EventProducer.instance = EventProducer()
        return EventProducer.instance

    def __init__(self):
        self._connection = None

    def attach_to_connection(self, event_broker: AbstractRobustConnection | None):
        self._connection = event_broker

    async def _send_customer_event(self, entity_uuid: str, routing_key: str) -> None:
        exchange_name = 'topic_customers'
        channel = await self._connection.channel()
        exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
        message = Message(entity_uuid.encode(ENCODING), delivery_mode=DeliveryMode.PERSISTENT)
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
    async def create_account(self, region: str, account_uuid: str, vip: bool) -> None:
        routing_key = f'create.account.{region}'
        routing_key += '.vip' if vip else '.standard'
        return await self._send_customer_event(account_uuid, routing_key)

    @decorate_event
    async def delete_account(self, region: str, account_uuid: str, vip: bool) -> None:
        routing_key = f'delete.account.{region}'
        routing_key += '.vip' if vip else '.standard'
        return await self._send_customer_event(account_uuid, routing_key)


class LocalEventProducer(EventProducer):

    async def _send_customer_event(self, entity_uuid: str, routing_key: str) -> None:
        logger.info(f'Stubbed. Sending the event with body={entity_uuid} to routing key={routing_key}')


def get_event_producer() -> EventProducer:
    return EventProducer.get_instance()


def get_local_event_producer() -> EventProducer:
    return LocalEventProducer()
