import pika
import os
import json

url = os.environ.get('CLOUDAMQP_URL')
params = pika.URLParameters(url)


class RabbitPublisher:

    def __init__(self) -> None:
        self.connection = None
        self.channel = None

    def publish(self, method, body) -> None:
        if self.connection is None:
            self.connection = pika.BlockingConnection(params)

        if self.channel is None:
            self.channel = self.connection.channel()

        properties = pika.BasicProperties(method)
        self.channel.basic_publish(exchange='', routing_key='main', body=json.dumps(body), properties=properties)
        print('Publishing event')
        print(json.dumps(body))

    def __del__(self) -> None:
        if self.connection:
            self.connection.close()
