import platform
import asyncio
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from consumer import Consumer

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

PORT = os.environ.get('PORT', '8070')
REGION = os.environ.get('REGION', 'emea')

app = FastAPI(
    title=f'{REGION}-billing-service',
    version='1.0',
    docs_url='/_swagger'
)


templates = Jinja2Templates(directory='templates')
consumer = Consumer(REGION, os.environ.get('CLOUDAMQP_URL'))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request,
                                                     'region': REGION,
                                                     'created_agents': consumer.created_agents,
                                                     'deleted_agents': consumer.deleted_agents,
                                                     'blocked_agents': consumer.blocked_agents,
                                                     'created_accounts': consumer.created_accounts,
                                                     'deleted_accounts': consumer.deleted_accounts,
                                                     })


@app.on_event("startup")
async def startup():
    loop = asyncio.get_running_loop()
    await consumer.wait_for_rabbit(loop, connection_timeout=5)

    await consumer.consume_create_agent(loop)
    await consumer.consume_delete_agent(loop)

    await consumer.consume_create_account(loop)
    await consumer.consume_delete_account(loop)

    await consumer.consume_block_agent(loop)
    await consumer.consume_unblock_agent(loop)


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
