import uvicorn
import os
from fastapi import FastAPI


PORT = os.environ.get('PORT', '8070')
REGION = os.environ.get('REGION', 'emea')

app = FastAPI(
    title='compliance-service',
    version='0.1',
    docs_url='/_swagger'
)


@app.get("/")
async def root():
    return {'msg': 'Hello my friend !'}


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(PORT),
        workers=1
    )
