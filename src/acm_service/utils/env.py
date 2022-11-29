import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.environ.get('AUTH_TOKEN', '')
TWO_FA = os.environ.get('TWO_FA', '')
CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', '')
SCOUT_KEY = os.environ.get('SCOUT_KEY', '')

PORT = os.environ.get('PORT', '8080')
ENABLE_EVENTS = os.environ.get('ENABLE_EVENTS', 'False')
ASYNC_DB_URL = os.environ.get('ASYNC_DB_URL', 'sqlite+aiosqlite:///./sql_app.db')
DEBUG_LOGGER_LEVEL = (os.environ.get('DEBUG_LOGGER_LEVEL', 'False') == 'True')
