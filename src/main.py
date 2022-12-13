from logging.config import dictConfig
import logging

import uvicorn

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from scout_apm.api import Config
from scout_apm.async_.starlette import ScoutMiddleware

from acm_service.utils.env import PORT
from acm_service.routers import accounts, agents
from acm_service.dependencies import get_event_broker_connection
from acm_service.utils.env import ENABLE_EVENTS, SCOUT_KEY, TWO_FA, API_TOKEN
from acm_service.utils.logconf import log_config, DEFAULT_LOGGER
from acm_service.utils.env import DEBUG_REST, DEBUG_LOGGER_LEVEL
from acm_service.utils.events.connection import disconnect_event_broker
from acm_service.utils.events.producer import get_event_producer, get_local_event_producer
from acm_service.utils.events.consumer import get_rabbit_consumer


dictConfig(log_config)
logger = logging.getLogger(DEFAULT_LOGGER)

app = FastAPI(
    debug=DEBUG_REST,
    title='account-management-service',
    version='1.0',
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
    logger.info(f'Application started with debugging: {DEBUG_LOGGER_LEVEL}, '
                f'debugging rest: {DEBUG_REST}, events: {ENABLE_EVENTS}')

    if len(API_TOKEN) == 0:
        logger.error('Missing API_TOKEN in your env variables')
    if len(TWO_FA) == 0:
        logger.error('Missing TWO_FA in your env variables')

    if ENABLE_EVENTS:
        logger.info('Connecting to event broker')
        event_broker = await get_event_broker_connection()

        logger.info('Subscribing to consume the events')
        consumer = get_rabbit_consumer()
        consumer.attach_to_connection(event_broker)
        await consumer.consume_block_agent()
        await consumer.consume_unblock_agent()

        logger.info('Preparing event producer')
        producer = get_event_producer()
        producer.attach_to_connection(event_broker)
    else:
        app.dependency_overrides[get_event_producer] = get_local_event_producer
        logger.info('Dispatching events was temporary disabled')


@app.on_event("shutdown")
async def shutdown_event():
    if ENABLE_EVENTS:
        await disconnect_event_broker()


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
