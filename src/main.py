import time
import fastapi
from fastapi import FastAPI
import uvicorn

from acm_service.sql_app.database import engine, Base
from acm_service.utils.env import PORT
from acm_service.routers import accounts

from timing_asgi import TimingMiddleware, TimingClient
from timing_asgi.integrations import StarletteScopeToName


class PrintTimings(TimingClient):
    def timing(self, metric_name, timing, tags):
        print(metric_name, timing, tags)


app = FastAPI(
    title='account-management',
    version='0.1',
    docs_url='/_swagger'
)
app.include_router(accounts.router)

app.add_middleware(
    TimingMiddleware,
    client=PrintTimings(),
    metric_namer=StarletteScopeToName(prefix="myapp", starlette_app=app)
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


#@app.middleware("http")
async def add_process_time_header(request: fastapi.Request, call_next) -> fastapi.Response:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


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
