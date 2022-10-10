import json
import pika
import os
import time


def main():
    params = pika.URLParameters(os.getenv('CLOUDAMQP_URL'))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='main', durable=True)

    def callback(ch, method, properties, body):
        print('Received in main')
        data = json.loads(body)
        print(data)
        time.sleep(20)
        print('Done')
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='main', on_message_callback=callback)
    print('Started consuming')

    channel.start_consuming()
    connection.close()


if __name__ == '__main__':
    main()
