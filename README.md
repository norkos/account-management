## What is this project about ?

The goal of the project was to play with the Microservice architecture and improve Python skills 

## What is used here?
- FastAPI
  - pagination for REST requests 
- Postgres
  - asyncio
  - alembic 
- pydantic and types
- decorators
- event handling implemented by RabbitMQ used in an async way
  - under `consumer` you might find async consumer
- Docker to make a smart environment: 
  - you can have your own e2e environment locally, 
  - or run the project with PyCharm with `main.py`, 
  - or deploy container into Heroku or ECS
- telemetry
   - Papertrail ![Papertrail](doc/papertrail.JPG) 
   - Scout ![Scout](doc/scout.JPG) 
   - Liberato ![Liberato](doc/liberato.JPG) 

## What is still on the TODO list?
- introduce caching
- play more with Heroku
  - check what resilience can be supported by Heroku
  - check if vertical/horizontal scaling can be supported by Heroku 
- add more consumers to the service and play with RabbitMQ topics
- deploy this to Amazon ECS
- pagination for DB synchronized with FastAPI pagination but leaving abstraction layer for the DB (to be deployed as Open Source)
- CORS

## How to run it
- to have all the environment in one place `docker-compose up`
  - because I don't want to control the order of the images in docker-compose, you might need to run alembic 
migrations by logging into `backend` docker image and running `upgrade_db.sh`
- for pytest please run `pytest`
- for Heroku please follow https://devcenter.heroku.com/articles/container-registry-and-runtime:
  - heroku login
  - heroku container:login
  - heroku create
  - define ENV variables in Heroku
       - create `AUTH_TOKEN` with token details needed to communicate with API
       - create `TWO_FA` with token needed to erase the DB
       - if you want to see debug logs set `DEBUG_LOGGER_LEVEL` into  `True`
  - install extensions in Heroku
    - (mandatory) postgres
       - create `ASYNC_DB_URL` in heroku EVN variables
    - (optional) rabbitMQ
       - set `ENABLE_EVENTS : True` in heroku EVN variable and create `CLOUDAMQP_URL` in heroku EVN variables 
    - (optional) Scout
  - heroku container:push web
  - heroku container:release web
  - heroku open
  
## Have fun ;)