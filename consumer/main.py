import uvicorn
import asyncio
import os
from fastapi import FastAPI

from consumer import Consumer

PORT = os.environ.get('PORT', '8070')


app = FastAPI(
    title='event-consumer',
    version='0.1',
    docs_url='/_swagger'
)


consumer = Consumer()


@app.get("/")
async def root():
    return {'Created accounts since I am alive: ': str(consumer.accounts())}


@app.on_event("startup")
async def startup():
    connection_timeout = 5
    queue_name = 'main'
    loop = asyncio.get_running_loop()
    await consumer.wait_for_rabbit(loop, connection_timeout)
    await consumer.consume(loop, queue_name)


@app.on_event("shutdown")
async def shutdown_event():
    await consumer.close()


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(PORT),
        workers=1
    )
