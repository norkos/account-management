import os

API_TOKEN = os.environ.get('NORKOS-AUTH-TOKEN', 'local')
PORT = os.environ.get('PORT', '8080')
CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', 'amqp://rabbitmq?connection_attempts=5&retry_delay=5')
