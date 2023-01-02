import asyncio

from fastapi.testclient import TestClient

from acm_service.dependencies import get_agent_dal, get_account_dal
from main import app


from acm_service.events.producer import get_event_producer

from unit_tests.utils import AccountDALStub, RabbitProducerStub, AgentDALStub

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


client = TestClient(app)
app.dependency_overrides[get_agent_dal] = override_agent_dal
app.dependency_overrides[get_account_dal] = override_account_dal
app.dependency_overrides[get_event_producer] = override_get_rabbit_producer
