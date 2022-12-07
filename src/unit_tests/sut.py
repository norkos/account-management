import asyncio

from fastapi.testclient import TestClient


from main import app

from acm_service.dependencies import get_account_dal, get_agent_dal, get_rabbit_producer
from unit_tests.utils import AccountDALStub, RabbitProducerStub, AgentDALStub

client = TestClient(app)
account_dal = AccountDALStub()
agent_dal = AgentDALStub()


def override_agent_dal():
    return agent_dal


def override_account_dal():
    return account_dal


def override_get_rabbit_producer():
    return RabbitProducerStub()


def reset_database():
    asyncio.run(account_dal.delete_all())
    asyncio.run(agent_dal.delete_all())


app.dependency_overrides[get_agent_dal] = override_agent_dal
app.dependency_overrides[get_account_dal] = override_account_dal
app.dependency_overrides[get_rabbit_producer] = override_get_rabbit_producer
