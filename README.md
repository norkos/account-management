## What this project is about  ?

Goal of the project was to play with Microservice architecture and improve Python skills 

## What I'm using in this Project ?
- FastAPI
- database with asyncio
- RabbitMQ used in async way
  - under `consumer` you might find async consumer 
- pydantic and types
- Docker, how to make smart environment: 
  - so you can locally have our own environment, 
  - or run the project with PyCharm, 
  - or deploy this to Heroku
- telemetry
   - Papertrail

## What is still on the TODO list ?
- extends telemetry with something like the Grafana dashboards
- check what resilience can be supported by Heroku
- check if vertical/horizontal scaling can be supported by Heroku 
- add more consumers to the service and play with RabbitMQ topics
- deploy this to Amazon ECS


## How to run it
- to have all environment in one place `docker-compose up`
- for pytest please run `pytest`
- for Heroku please follow https://devcenter.heroku.com/articles/container-registry-and-runtime:
  - heroku login
  - heroku container:login
  - heroku create
  - heroku container:push web
  - heroku container:release web
  - heroku open
  
## Have fun ;)