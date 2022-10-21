from fastapi import FastAPI
import uvicorn

from acm_service.sql_app.database import engine, Base
from acm_service.utils.env import PORT
from acm_service.routers import accounts
from acm_service.dependencies import get_local_rabbit_producer, get_rabbit_producer


app = FastAPI(
    title='account-management',
    version='0.1',
    docs_url='/_swagger'
)
app.include_router(accounts.router)
app.dependency_overrides[get_rabbit_producer] = get_local_rabbit_producer


@app.on_event("startup")
async def startup():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {'msg': 'Hello my friend !'}


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(PORT),
        workers=2
    )
