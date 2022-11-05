from fastapi import FastAPI
import uvicorn

from acm_service.sql_app.database import engine, Base
from acm_service.utils.env import PORT
from acm_service.routers import accounts
from acm_service.dependencies import get_local_rabbit_producer, get_rabbit_producer
from acm_service.utils.env import ENABLE_EVENTS, SCOUT_KEY, API_TOKEN
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

Config.set(
    key=SCOUT_KEY,
    name=app.title,
    monitor=True,
)
app.add_middleware(ScoutMiddleware)


@app.on_event("startup")
async def startup():
    if ENABLE_EVENTS == 'False':
        app.dependency_overrides[get_rabbit_producer] = get_local_rabbit_producer
        logger.info('Dispatching events was temporary disabled, '
                    'so that we won do not worry about RabbitMQ message limits in our PaaS provider')

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


# https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html?highlight=create_async_engine
@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()


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
