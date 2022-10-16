from acm_service.sql_app.database import async_session
from acm_service.sql_app.account_dal import AccountDAL


async def get_db():
    async with async_session() as session:
        async with session.begin():
            yield AccountDAL(session)
