import asyncio

from aio_pika.abc import AbstractRobustConnection
from aioredis import Redis
from fastapi import Header

from acm_service.utils.env import AUTH_TOKEN, TWO_FA
from acm_service.utils.http_exceptions import raise_bad_request
from acm_service.events.connection import connect_to_rabbit_mq
from acm_service.cache.connection import connect_to_redis
from acm_service.cache.repositories import AgentCachedRepository, AccountCachedRepository
from acm_service.data_base.repositories import AccountRepository, AgentRepository
from acm_service.services.agent_service import AgentService
from acm_service.events.producer import get_event_producer
from acm_service.services.account_service import AccountService


async def get_cache_connection() -> Redis | None:
    return await connect_to_redis()


async def get_event_broker_connection() -> AbstractRobustConnection | None:
    return await connect_to_rabbit_mq(asyncio.get_event_loop())


def get_token_header(x_token: str = Header()) -> None:
    if x_token != AUTH_TOKEN:
        raise_bad_request("Invalid X-Token header")


def get_2fa_token_header(two_fa: str = Header()) -> None:
    if two_fa != TWO_FA:
        raise_bad_request("Invalid 2FA header")


def get_cached_agent_repository() -> AgentRepository:
    return AgentCachedRepository()


def get_cached_account_repository() -> AccountRepository:
    return AccountCachedRepository()


def get_account_repository() -> AccountRepository:
    return AccountRepository()


def get_agent_repository() -> AgentRepository:
    return AgentRepository()


def get_agent_service() -> AgentService:
    return AgentService(get_agent_repository(), get_account_repository(), get_event_producer())


def get_account_service() -> AccountService:
    return AccountService(get_agent_repository(), get_account_repository(), get_event_producer())


def get_agent_service_with_cache() -> AgentService:
    return AgentService(get_cached_agent_repository(), get_cached_account_repository(), get_event_producer())


def get_account_service_with_cache() -> AccountService:
    return AccountService(get_cached_agent_repository(), get_cached_account_repository(), get_event_producer())
