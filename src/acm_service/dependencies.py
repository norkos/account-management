from fastapi import Header

from acm_service.sql_app.database import async_session
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.sql_app.agent_dal import AgentDAL
from acm_service.utils.env import CLOUDAMQP_URL
from acm_service.utils.events.producer import RabbitProducer, LocalRabbitProducer
from acm_service.utils.env import API_TOKEN, TWO_FA
from acm_service.utils.http_exceptions import raise_bad_request


async def get_account_dal() -> AccountDAL:
    async with async_session() as session:
        async with session.begin():
            yield AccountDAL(session)


async def get_agent_dal() -> AgentDAL:
    async with async_session() as session:
        async with session.begin():
            yield AgentDAL(session)


async def get_rabbit_producer() -> RabbitProducer:
    return RabbitProducer(CLOUDAMQP_URL)


async def get_local_rabbit_producer() -> RabbitProducer:
    return LocalRabbitProducer()


async def get_token_header(x_token: str = Header()) -> None:
    if x_token != API_TOKEN:
        raise_bad_request("Invalid X-Token header")


async def get_2fa_token_header(two_fa: str = Header()) -> None:
    if two_fa != TWO_FA:
        raise_bad_request("Invalid 2FA header")
