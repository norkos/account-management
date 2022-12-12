## What is this project about ?

The goal of the project was to play with the Microservice architecture and improve Python skills 

### User stories

1. As a customer I'd like to use account-management-service REST API to create the frontend (DONE)
2. As a billing team I'd like to be updated regarding both Accounts and Agents, so I can calculate invoices (DONE)
3. As a compliance office I'd like to be able to block Agent if agent account is hacked, so agent won't be charged to the extra usage (DONE)
4. As a Success Manager I'd like to be informed about creating and removing VIP accounts, so I can calculate key customer turnover (DONE)

### Architecture

#### Target Diagram
![Papertrail](doc/arch.jpeg)
https://lucid.app/lucidchart/388b7cea-029a-46ae-95e5-0c50148fb8cb/edit?viewport_loc=-176%2C-119%2C3072%2C1551%2CCFRzE~qEaxOQ&invitationId=inv_700a331f-39a6-41a5-a14a-7c5007f38322

#### Data model
<img src="doc/data.JPG" height="300"></img>
- Agent e-mail is unique among all Agents from all Accounts
- Account e-mail is unique among all others Accounts 

### What is used here?
- FastAPI
  - pagination for REST requests
- Postgres
  - asyncio
  - alembic
- pydantic
- types
- decorators
- unit tests realized with pytest
  - fixtures
  - mocks
- integration tests
- event handling implemented by RabbitMQ used in an async way using Topics
  - under `demo_environment/billing_service` you get consumer for accounts/agents Topics (user story 2.)
  - under `demo_environment/compliance_service` you get producer for blocking agents (user story 3.)
  - under `demo_environment/vip_customer_service` you get consumer for VIP accounts (user story 4.)
- Docker to make a smart environment: 
  - you can have your own e2e environment locally, 
  - or run the project with PyCharm with `main.py`, 
  - or deploy container into Heroku or ECS
- telemetry
   - Papertrail ![Papertrail](doc/papertrail.JPG) 
   - Scout ![Scout](doc/scout.JPG) 
   - Liberato ![Liberato](doc/liberato.JPG) 

### TODO list
- https://locust.io/ to make load testing
- play more with Heroku
  - check what resilience can be supported by Heroku
  - check if vertical/horizontal scaling can be supported by Heroku
  - Redis ?
- deploy this to Amazon ECS
- pagination for DB synchronized with FastAPI pagination but leaving abstraction layer for the DB (to be deployed as Open Source)

### How to run it
- to have all the environment in one place `docker-compose -f docker-compose-demo.yml up`
  - to run DB migrations execute CLI on `backend` docker image by running `migrate_db.sh`
  - REST is exposed by Swagger in http://localhost:9090/_swagger

### How to test it
- for unit tests: 
  - `pytest src/unit_tests`
- for integration tests: 
  - `docker-compose -f docker-compose-integration.yml up`
  - run DB migrations execute CLI on `backend` docker image by running `migrate_db.sh`
  - execute command on `rabbitmq` docker: `rabbitmqctl set_user_tags guest administrator`
  - `pytest src/integration_tests/test_flows.py`


### How to deploy it
- for Heroku please follow https://devcenter.heroku.com/articles/container-registry-and-runtime:
  - heroku login
  - heroku container:login
  - heroku create
  - heroku container:push web
  - define ENV variables in Heroku
       - create `AUTH_TOKEN` with token details needed to communicate with RESTAPI
       - create `TWO_FA` with token needed to erase the DB
       - if you want to see debug logs set `DEBUG_LOGGER_LEVEL` into  `True`
       - if you want FastAPI to be verbose when sending response with code 500 set `DEBUG_REST` into `True`
  - install extensions in Heroku
    - (mandatory) postgres
       - create `ASYNC_DB_URL` in heroku EVN variables
    - (optional) rabbitMQ
       - set `ENABLE_EVENTS` to True in heroku EVN variable and create `CLOUDAMQP_URL` in heroku EVN variables 
    - (optional) Scout
  - heroku container:release web
  - open https://{your_heroku_app}/_swagger and play using `AUTH_TOKEN`
  
### Have fun ;)