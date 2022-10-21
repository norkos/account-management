import json
import aio_pika


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


class LocalRabbitProducer(RabbitProducer):

    def __init__(self):
        super().__init__('')

    async def async_publish(self, method, body) -> None:
        print(f'Sending the event to main: {body}')
