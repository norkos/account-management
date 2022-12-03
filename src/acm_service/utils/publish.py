import asyncio
import json
import aio_pika
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
        connection = await aio_pika.connect_robust(self._url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(body).encode()
                ),
                routing_key='main'
            )
            logger.info(f'Sending the event to queue: {body}')


class LocalRabbitProducer(RabbitProducer):

    def __init__(self):
        super().__init__('')

    async def async_publish(self, method, body) -> None:
        logger.info(f'Sending the event to queue: {body}')
