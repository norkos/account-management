import logging
from typing import Callable

from aio_pika import ExchangeType
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.controllers.agent_controller import AgentController
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.sql_app.agent_dal import AgentDAL
from acm_service.sql_app.database import async_session
from acm_service.utils.events.producer import get_event_producer
from acm_service.utils.env import ENCODING

logger = logging.getLogger(DEFAULT_LOGGER)


def decode(message: AbstractIncomingMessage) -> str:
    return message.body.decode(ENCODING)


class EventConsumer:

    instance = None

    @classmethod
    def get_instance(cls):
        if EventConsumer.instance is None:
            EventConsumer.instance = EventConsumer()
        return EventConsumer.instance

    def __init__(self):
        self._connection = None

    def attach_to_connection(self, event_broker: AbstractRobustConnection | None):
        self._connection = event_broker

    async def _block_agent(self, message: AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            logger.info(f'Receiving event to block agent: {uuid}')

            async with async_session() as session:
                async with session.begin():
                    agents = AgentDAL(session)
                    accounts = AccountDAL(session)
                    controller = AgentController(agents, accounts, get_event_producer())
                    result = await controller.block_agent(uuid)
                    logger.info(f'Receiving event to block agent: {uuid} with result: {result}')

    async def _unblock_agent(self, message: AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            logger.info(f'Receiving event to block agent: {uuid}')

            async with async_session() as session:
                async with session.begin():
                    agents = AgentDAL(session)
                    accounts = AccountDAL(session)
                    controller = AgentController(agents, accounts, get_event_producer())
                    result = await controller.unblock_agent(uuid)
                    logger.info(f'Receiving event to block agent: {uuid} with result: {result}')

    async def consume_block_agent(self) -> None:
        await self.consume(binding_key='block.agent', callback=self._block_agent)

    async def consume_unblock_agent(self) -> None:
        await self.consume(binding_key='unblock.agent', callback=self._unblock_agent)

    async def consume(self, binding_key: str, callback: Callable) -> None:
        if self._connection is None:
            logger.warning('Cannot bind for the queues due to missing broker connection')
            return

        queue_name = f'{binding_key}_queue'
        topic_name = 'topic_compliance'

        channel = await self._connection.channel()
        exchange = await channel.declare_exchange(name=topic_name, type=ExchangeType.TOPIC)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=binding_key)
        await queue.consume(callback)
        logger.info(f'Biding as the consumer to: {binding_key} from {topic_name}')

    async def close(self):
        if self._connection:
            await self._connection.close()


def get_rabbit_consumer() -> EventConsumer:
    return EventConsumer.get_instance()