import asyncio
import os
import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TOKEN = os.environ.get('AUTH_TOKEN', 'local')
URL = os.environ.get('URL', 'http://localhost:8080')
RABBIT_MQ = 'amqp://localhost?connection_attempts=5&retry_delay=5'
