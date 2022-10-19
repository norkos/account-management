from acm_service.sql_app.database import async_session
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.utils.env import CLOUDAMQP_URL
from acm_service.utils.publish import RabbitProducer


async def get_db():
    async with async_session() as session:
        async with session.begin():
            yield AccountDAL(session)


async def get_rabbit_producer():
    return RabbitProducer(CLOUDAMQP_URL)
