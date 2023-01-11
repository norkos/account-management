from logging.config import dictConfig
import logging

import uvicorn

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from scout_apm.api import Config
from scout_apm.async_.starlette import ScoutMiddleware

from acm_service.utils.env import PORT, REDIS_URL
from acm_service.routers import accounts, agents, dev
from acm_service.dependencies import get_event_broker_connection, \
    get_cache_connection, get_agent_service, get_account_service, get_agent_service_with_cache, \
    get_account_service_with_cache
from acm_service.utils.env import ENABLE_EVENTS, SCOUT_KEY, TWO_FA, AUTH_TOKEN
from acm_service.utils.logconf import log_config, DEFAULT_LOGGER
from acm_service.utils.env import DEBUG_REST, DEBUG_LOGGER_LEVEL
from acm_service.events.connection import disconnect_event_broker
from acm_service.events.producer import get_event_producer, get_local_event_producer
from acm_service.events.consumer import get_rabbit_consumer
from acm_service.cache.repositories import Cache

dictConfig(log_config)
logger = logging.getLogger(DEFAULT_LOGGER)

app = FastAPI(
    debug=DEBUG_REST,
    title='account-management-service',
    version='1.1',
    docs_url='/_swagger'
)
app.include_router(accounts.router)
app.include_router(agents.router)
app.include_router(dev.router)

Config.set(
    key=SCOUT_KEY,
    name=app.title,
    monitor=True,
)
app.add_middleware(ScoutMiddleware)
add_pagination(app)

# https://www.cloudamqp.com/blog/part1-rabbitmq-best-practice.html -> keep connection separated
consumer_connection = None
producer_connection = None


async def prepare_event_consumer():
    logger.info('Connecting to event broker')
    global consumer_connection
    consumer_connection = await get_event_broker_connection()
    consumer = get_rabbit_consumer()
    consumer.attach_to_connection(consumer_connection)
    await consumer.consume_block_agent()
    await consumer.consume_unblock_agent()
    logger.info('Subscribed to consume the events')


async def prepare_event_producer():
    logger.info('Preparing event producer')
    global producer_connection
    producer_connection = await get_event_broker_connection()
    producer = get_event_producer()
    producer.attach_to_connection(producer_connection)
    logger.info('Event producer ready')


async def prepare_cache():
    logger.info('Preparing cache')
    cache_connection = await get_cache_connection()
    if cache_connection is None:
        logger.error('Cannot connect to cache service. Running without it.')
        return

    Cache.get_instance().connect_to_cache_service(cache_connection)
    app.dependency_overrides[get_agent_service] = get_agent_service_with_cache
    app.dependency_overrides[get_account_service] = get_account_service_with_cache
    logger.info('Cache is ready')


@app.on_event("startup")
async def startup():
    logger.info(f'Application started with debugging: {DEBUG_LOGGER_LEVEL}, '
                f'debugging rest: {DEBUG_REST}, events: {ENABLE_EVENTS}')

    if len(AUTH_TOKEN) == 0:
        logger.error('Missing AUTH_TOKEN in your env variables')
    if len(TWO_FA) == 0:
        logger.error('Missing TWO_FA in your env variables')

    if ENABLE_EVENTS:
        await prepare_event_consumer()
        await prepare_event_producer()
    else:
        app.dependency_overrides[get_event_producer] = get_local_event_producer
        logger.info('Dispatching events was temporary disabled')

    if len(REDIS_URL) != 0:
        await prepare_cache()


@app.on_event("shutdown")
async def shutdown_event():
    if ENABLE_EVENTS:
        await disconnect_event_broker(producer_connection)
        await disconnect_event_broker(consumer_connection)


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
