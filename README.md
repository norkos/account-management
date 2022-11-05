## What is this project about ?

The goal of the project was to play with the Microservice architecture and improve Python skills 

## What is used here?
- FastAPI
- database with asyncio
- RabbitMQ used in an async way
  - under `consumer` you might find async consumer 
- pydantic and types
- Docker, how to make a smart environment: 
  - so you can have your own e2e environment locally, 
  - or run the project with PyCharm with `main.py`, 
  - or deploy container into Heroku
- telemetry
   - Papertrail ![Papertrail](doc/papertrail.JPG) 
   - Scout ![Scout](doc/scout.JPG) 
   - Liberato ![Liberato](doc/liberato.JPG) 

## What is still on the TODO list?
- introduce alembic
- introduce caching
- play more with Heroku
  - extends telemetry with something like the Grafana dashboards (let's see what Heroku has)
  - check what resilience can be supported by Heroku
  - check if vertical/horizontal scaling can be supported by Heroku 
- add more consumers to the service and play with RabbitMQ topics
- deploy this to Amazon ECS


## How to run it
- to have all the environment in one place `docker-compose up`
- for pytest please run `pytest`
- for Heroku please follow https://devcenter.heroku.com/articles/container-registry-and-runtime:
  - heroku login
  - heroku container:login
  - heroku create
  - heroku container:push web
  - heroku container:release web
  - heroku open
  
## Have fun ;)