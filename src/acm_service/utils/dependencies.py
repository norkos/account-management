import asyncio

from aio_pika.abc import AbstractRobustConnection
from aioredis import Redis
from fastapi import Header

from acm_service.utils.env import AUTH_TOKEN, TWO_FA
from acm_service.utils.http_exceptions import raise_bad_request
from acm_service.utils.events.connection import connect_to_rabbit_mq
from acm_service.utils.cache.connection import connect_to_redis
from acm_service.accounts.repository import AccountRepository, AccountCachedRepository
from acm_service.agents.repository import AgentRepository, AgentCachedRepository
from acm_service.agents.service import AgentService
from acm_service.utils.events.producer import get_event_producer
from acm_service.accounts.service import AccountService


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


def get_agent_service() -> AgentService:
    return AgentService(AgentRepository(), AccountRepository(), get_event_producer())


def get_account_service() -> AccountService:
    return AccountService(AgentRepository(), AccountRepository(), get_event_producer())


def get_agent_service_with_cache() -> AgentService:
    return AgentService(AgentCachedRepository(), AccountCachedRepository(), get_event_producer())


def get_account_service_with_cache() -> AccountService:
    return AccountService(AgentCachedRepository(), AccountCachedRepository(), get_event_producer())
