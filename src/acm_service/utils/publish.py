import json
import aio_pika
from acm_service.utils.logconf import DEFAULT_LOGGER

import logging
logger = logging.getLogger(DEFAULT_LOGGER)


class RabbitProducer:

    def __init__(self, url: str):
        self._url = url

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
