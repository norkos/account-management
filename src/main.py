from fastapi import FastAPI
import uvicorn
from fastapi_pagination import add_pagination

from acm_service.utils.env import PORT
from acm_service.routers import accounts, agents
from acm_service.dependencies import get_local_rabbit_producer, get_rabbit_producer
from acm_service.utils.env import ENABLE_EVENTS, SCOUT_KEY, TWO_FA, API_TOKEN
from acm_service.utils.logconf import log_config, DEFAULT_LOGGER

from scout_apm.api import Config
from scout_apm.async_.starlette import ScoutMiddleware

from logging.config import dictConfig
import logging


dictConfig(log_config)
logger = logging.getLogger(DEFAULT_LOGGER)


app = FastAPI(
    title='account-management',
    version='0.1',
    docs_url='/_swagger'
)
app.include_router(accounts.router)
app.include_router(agents.router)

Config.set(
    key=SCOUT_KEY,
    name=app.title,
    monitor=True,
)
app.add_middleware(ScoutMiddleware)
add_pagination(app)


@app.on_event("startup")
async def startup():
    logger.info(f'Application started')
    if len(API_TOKEN) == 0:
        logger.error(f'Missing API_TOKEN in your env variables')
    if len(TWO_FA) == 0:
        logger.error(f'Missing TWO_FA in your env variables')

    if ENABLE_EVENTS == 'False':
        app.dependency_overrides[get_rabbit_producer] = get_local_rabbit_producer
        logger.info('Dispatching events was temporary disabled, '
                    'so that we won do not worry about RabbitMQ message limits in our PaaS provider')


@app.get("/")
async def root():
    return {'msg': 'Hello my friend !'}


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(PORT),
        workers=1
    )
