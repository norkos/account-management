import os

API_TOKEN = os.environ.get('NORKOS-AUTH-TOKEN', 'local')
PORT = os.environ.get('PORT', '8080')
CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', '')
ENABLE_EVENTS = os.environ.get('ENABLE_EVENTS', 'False')
ASYNC_DB_URL = os.environ.get('ASYNC_DB_URL', 'sqlite+aiosqlite:///./sql_app.db')
DEBUG_LOGGER_LEVEL = (os.environ.get('DEBUG_LOGGER_LEVEL', 'False') == 'True')
