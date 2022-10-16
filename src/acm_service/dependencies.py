from acm_service.sql_app.database import AsyncLocalSession


async def get_db():
    async with AsyncLocalSession() as session:
        async with session.begin():
            yield session
