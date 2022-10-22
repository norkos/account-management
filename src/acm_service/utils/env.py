import os

API_TOKEN = os.environ.get('NORKOS-AUTH-TOKEN', 'local')
PORT = os.environ.get('PORT', '8080')
CLOUDAMQP_URL = os.environ.get('CLOUDAMQP_URL', '')
ASYNC_DB_URL = os.environ.get('ASYNC_DB_URL', 'sqlite+aiosqlite:///./sql_app.db')
