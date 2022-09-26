import os

os.environ['NORKOS-AUTH-TOKEN'] = 'for_unit_tests'
os.environ['CLOUDAMQP_URL'] = 'amqp://rabbitmq?connection_attempts=5&retry_delay=5'