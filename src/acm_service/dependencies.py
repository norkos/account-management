import asyncio

from aio_pika.abc import AbstractRobustConnection
from aioredis import Redis
from fastapi import Header


from acm_service.utils.env import AUTH_TOKEN, TWO_FA
from acm_service.utils.http_exceptions import raise_bad_request
from acm_service.events.connection import connect_to_rabbit_mq
from acm_service.cache.connection import connect_to_redis
from acm_service.cache.cached_dal import AgentCachedRepository, AccountCachedRepository
from acm_service.data_base.repositories import AccountRepository, AgentRepository


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


def get_cached_agent_dal() -> AgentRepository:
    return AgentCachedRepository()


def get_cached_account_dal() -> AccountRepository:
    return AccountCachedRepository()


def get_account_dal() -> AccountRepository:
    return AccountRepository()


def get_agent_dal() -> AgentRepository:
    return AgentRepository()
