import asyncio
import logging

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection

from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.utils.env import CLOUDAMQP_URL, CLOUDAMQP_RETRIES, CLOUDAMQP_TIMEOUT

logger = logging.getLogger(DEFAULT_LOGGER)


async def connect_to_rabbit_mq(loop, url: str = CLOUDAMQP_URL, connection_timeout: int = CLOUDAMQP_TIMEOUT,
                               retries: int = CLOUDAMQP_RETRIES) -> AbstractRobustConnection | None:
    for x in range(retries):
        try:
            connection = await connect_robust(CLOUDAMQP_URL, loop=loop)
            logger.info('RabbitMq is alive !')
            return connection
        except Exception as _error:
            logger.info(f'Waiting for event broker to be alive. '
                        f'Sleeping {connection_timeout} seconds before {x + 1} retry.')
            await asyncio.sleep(connection_timeout)
    logger.error(f'Failed to connect to event broker: {url}')
    return None


async def disconnect_event_broker(connection: AbstractRobustConnection | None):
    if connection:
        await connection.close()
