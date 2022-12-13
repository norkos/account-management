import asyncio

from aio_pika.abc import AbstractRobustConnection
from fastapi import Header

from acm_service.sql_app.database import async_session
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.sql_app.agent_dal import AgentDAL

from acm_service.utils.env import API_TOKEN, TWO_FA
from acm_service.utils.http_exceptions import raise_bad_request
from acm_service.utils.events.connection import connect_to_event_broker


async def get_account_dal() -> AccountDAL:
    async with async_session() as session:
        async with session.begin():
            yield AccountDAL(session)


async def get_agent_dal() -> AgentDAL:
    async with async_session() as session:
        async with session.begin():
            yield AgentDAL(session)


async def get_event_broker_connection() -> AbstractRobustConnection | None:
    return await connect_to_event_broker(asyncio.get_event_loop())


async def get_local_event_broker_connection() -> None:
    return None


def get_token_header(x_token: str = Header()) -> None:
    if x_token != API_TOKEN:
        raise_bad_request("Invalid X-Token header")


def get_2fa_token_header(two_fa: str = Header()) -> None:
    if two_fa != TWO_FA:
        raise_bad_request("Invalid 2FA header")
