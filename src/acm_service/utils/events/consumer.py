from typing import Callable

import aio_pika
import asyncio

from aio_pika import connect_robust, ExchangeType
from acm_service.utils.logconf import DEFAULT_LOGGER

import logging

from acm_service.controllers.agent_controller import AgentController
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.sql_app.agent_dal import AgentDAL
from acm_service.sql_app.database import async_session
from acm_service.dependencies import get_rabbit_producer

logger = logging.getLogger(DEFAULT_LOGGER)


def decode(message: aio_pika.abc.AbstractIncomingMessage) -> str:
    return message.body.decode('utf-8')


class Consumer:
    def __init__(self, url: str):
        self._url = url
        self._connection = None

    async def wait_for_rabbit(self, loop, connection_timeout: int) -> None:
        while True:
            try:
                connection = await aio_pika.connect_robust(self._url, loop=loop)
                await connection.close()
                logger.info('RabbitMq is alive !')
                return
            except Exception as error:
                logger.info(f'Waiting for RabbitMQ to be alive. Sleeping {connection_timeout} seconds before retry.')
                await asyncio.sleep(connection_timeout)

    async def block_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            logger.info(f'Receiving event to block agent: {uuid}')

            async with async_session() as session:
                async with session.begin():
                    agents = AgentDAL(session)
                    accounts = AccountDAL(session)
                    controller = AgentController(agents, accounts, get_rabbit_producer())
                    result = await controller.block_agent(uuid)
                    logger.info(f'Receiving event to block agent: {uuid} with result: {result}')

    async def unblock_agent(self, message: aio_pika.abc.AbstractIncomingMessage, ) -> None:
        async with message.process():
            uuid = decode(message)
            logger.info(f'Receiving event to block agent: {uuid}')

            async with async_session() as session:
                async with session.begin():
                    agents = AgentDAL(session)
                    accounts = AccountDAL(session)
                    controller = AgentController(agents, accounts, get_rabbit_producer())
                    result = await controller.unblock_agent(uuid)
                    logger.info(f'Receiving event to block agent: {uuid} with result: {result}')

    async def consume_block_agent(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'block.agent', callback=self.block_agent)

    async def consume_unblock_agent(self, loop) -> None:
        await self.consume(loop,
                           binding_key=f'unblock.agent', callback=self.unblock_agent)

    async def consume(self, loop, binding_key: str, callback: Callable) -> None:
        queue_name = f'{binding_key}_queue'
        topic_name = 'topic_compliance'

        self._connection = await connect_robust(self._url, loop=loop)
        channel = await self._connection.channel()
        exchange = await channel.declare_exchange(name=topic_name, type=ExchangeType.TOPIC)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=binding_key)
        await queue.consume(callback)
        logger.info(f'Biding as the consumer to: {binding_key} from {topic_name}')

    async def close(self):
        if self._connection:
            await self._connection.close()
