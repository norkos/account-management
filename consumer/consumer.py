import json
import pika
import os


def main():
    params = pika.URLParameters(os.getenv('CLOUDAMQP_URL'))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='main', durable=True)

    def callback(ch, method, properties, body):
        print('Received in main')
        data = json.loads(body)
        print(data)

    channel.basic_consume(queue='main', on_message_callback=callback, auto_ack=True)
    print('Started consuming')

    channel.start_consuming()
    connection.close()


if __name__ == '__main__':
    main()
