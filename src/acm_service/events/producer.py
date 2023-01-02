import asyncio
import logging
from uuid import uuid4, UUID

from aio_pika import ExchangeType, Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.env import ENCODING, CLOUDAMQP_RETRIES, CLOUDAMQP_TIMEOUT
from acm_service.data_base.schemas import RegionEnum

logger = logging.getLogger(DEFAULT_LOGGER)


def decorate_event(send_event):
    async def wrapper(*args, **kwargs):
        retries = CLOUDAMQP_RETRIES
        time_out = CLOUDAMQP_TIMEOUT
        retry = 0
        ex = None
        while retry < retries:
            try:
                return await send_event(*args, **kwargs)
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

    async def _send_customer_event(self, entity_uuid: UUID | None, routing_key: str) -> None:
        exchange_name = 'topic_customers'
        channel = await self._connection.channel()
        message_content = str(entity_uuid) if entity_uuid else '*'

        exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.TOPIC)
        message = Message(message_content.encode(ENCODING), delivery_mode=DeliveryMode.PERSISTENT)
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f'Sending the event with body={message_content} to routing key={routing_key}')

    @decorate_event
    async def block_agent(self, region: RegionEnum, agent_uuid: UUID) -> None:
        routing_key = f'block.agent.{region.value}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def unblock_agent(self, region: RegionEnum, agent_uuid: UUID) -> None:
        routing_key = f'unblock.agent.{region.value}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def create_agent(self, region: RegionEnum, agent_uuid: UUID) -> None:
        routing_key = f'create.agent.{region.value}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def delete_agent(self, region: RegionEnum | None,
                           agent_uuid: UUID | None) -> None:
        routing_key = f'delete.agent.{region.value if region else "*"}'
        return await self._send_customer_event(agent_uuid, routing_key)

    @decorate_event
    async def create_account(self, region: RegionEnum, account_uuid: UUID, vip: bool) -> None:
        routing_key = f'create.account.{region.value}'
        routing_key += '.vip' if vip else '.standard'
        return await self._send_customer_event(account_uuid, routing_key)

    @decorate_event
    async def delete_account(self, region: RegionEnum | None,
                             account_uuid: UUID | None, vip: bool) -> None:
        routing_key = f'delete.account.{region.value if region else "*"}'
        routing_key += '.vip' if vip else '.standard'
        return await self._send_customer_event(account_uuid, routing_key)


class LocalEventProducer(EventProducer):

    async def _send_customer_event(self, entity_uuid: UUID, routing_key: str) -> None:
        logger.info(f'Stubbed. Sending the event with body={entity_uuid} to routing key={routing_key}')


def get_event_producer() -> EventProducer:
    return EventProducer.get_instance()


def get_local_event_producer() -> EventProducer:
    return LocalEventProducer()
