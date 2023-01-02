import os
from dotenv import load_dotenv

load_dotenv()

ENCODING = 'utf-8'
AUTH_TOKEN = os.environ.get('AUTH_TOKEN', '')
TWO_FA = os.environ.get('TWO_FA', '')

CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', '')
CLOUDAMQP_RETRIES = int(os.environ.get('CLOUDAMQP_RETRIES', 1))
CLOUDAMQP_TIMEOUT = int(os.environ.get('CLOUDAMQP_TIMEOUT', 0))

SCOUT_KEY = os.environ.get('SCOUT_KEY', '')

PORT = os.environ.get('PORT', '8080')
ENABLE_EVENTS = os.environ.get('ENABLE_EVENTS', 'False') == 'True'
ASYNC_DB_URL = os.environ.get('ASYNC_DB_URL', 'sqlite+aiosqlite:///./sql_app.db')
DEBUG_LOGGER_LEVEL = (os.environ.get('DEBUG_LOGGER_LEVEL', 'False') == 'True')
DEBUG_REST = (os.environ.get('DEBUG_REST', 'False') == 'True')

REDIS_URL = os.environ.get('REDIS_URL', '')
REDIS_PORT = os.environ.get('REDIS_PORT', '')
REDIS_RETRIES = int(os.environ.get('CLOUDAMQP_RETRIES', 1))
REDIS_TIMEOUT = int(os.environ.get('CLOUDAMQP_TIMEOUT', 0))
REDIS_CACHE_INVALIDATION_IN_SECONDS = int(os.environ.get('REDIS_CACHE_INVALIDATION_IN_SECONDS', 60))
