import asyncio
import logging

from redis import Redis

from acm_service.utils.env import REDIS_URL, REDIS_PORT, REDIS_RETRIES, REDIS_TIMEOUT
from acm_service.utils.logconf import DEFAULT_LOGGER

logger = logging.getLogger(DEFAULT_LOGGER)


async def connect_to_redis(url: str = REDIS_URL, port: int = REDIS_PORT, connection_timeout: int = REDIS_TIMEOUT,
                           retries: int = REDIS_RETRIES) -> Redis | None:
    for x in range(retries):
        try:
            connection = Redis(host=url, port=port,
                               decode_responses=True,
                               single_connection_client=True)
            logger.info('Redis is alive !')
            return connection
        except Exception as _error:
            logger.info(f'Waiting for Redis to be alive. '
                        f'Sleeping {connection_timeout} seconds before {x + 1} retry.')
            await asyncio.sleep(connection_timeout)
    logger.error(f'Failed to connect to Redis: {url}')
    return None
