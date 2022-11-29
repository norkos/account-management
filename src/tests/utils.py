from uuid import uuid4
from typing import List

from pydantic import EmailStr, UUID4
from sqlalchemy.orm import Session
from acm_service.sql_app.account_dal import AccountDAL
from acm_service.sql_app.agent_dal import AgentDAL
from acm_service.sql_app.models import Account, Agent
from acm_service.utils.publish import RabbitProducer
from acm_service.sql_app.schemas import AccountWithoutAgents


class LocalDB:
    def __init__(self):
        self._entity_by_uuid = {}
        self._entity_by_mail = {}

    @property
    def entity_by_uuid(self):
        return self._entity_by_uuid

    @property
    def entity_by_mail(self):
        return self._entity_by_mail

    def reset(self):
        self._entity_by_uuid = {}
        self._entity_by_mail = {}


class AgentDB(LocalDB):
    def create_random_parent(self) -> str:
        raw_account = {
            'name': 'dummy_name',
            'email': 'dummy_mail@wp.pl',
            'id': str(uuid4())
        }
        account = AccountWithoutAgents.parse_obj(raw_account)
        return str(account.id)


class AccountDB(LocalDB):
    pass


class RabbitProducerStub(RabbitProducer):

    def __init__(self):
        super().__init__('')

    async def async_publish(self, method, body) -> None:
        pass


class AccountDALStub(AccountDAL):
    class SessionStub(Session):
        pass

    def __init__(self, local_db: AccountDB):
        super().__init__(self.SessionStub())
        self._accounts_by_uuid = local_db.entity_by_uuid
        self._accounts_by_mail = local_db.entity_by_mail

    async def create(self, **kwargs) -> Account:
        new_account = Account(id=str(uuid4()), **kwargs)
        self._accounts_by_uuid[new_account.id] = new_account
        self._accounts_by_mail[new_account.email] = new_account
        return new_account

    async def get(self, uuid: str) -> Account | None:
        if uuid in self._accounts_by_uuid:
            return self._accounts_by_uuid[uuid]
        return None

    async def get_account_by_email(self, email: str) -> Account | None:
        if email in self._accounts_by_mail:
            return self._accounts_by_mail[email]
        return None

    async def get_all(self) -> List[Account]:
        return list(self._accounts_by_uuid.values())

    async def delete(self, uuid: str):
        if uuid in self._accounts_by_uuid:
            del self._accounts_by_uuid[uuid]

    async def update(self, uuid: str, **kwargs):
        new_account = Account(uuid, **kwargs)
        self._accounts_by_uuid[new_account.id] = new_account
        self._accounts_by_mail[new_account.email] = new_account
        return new_account


class AgentDALStub(AgentDAL):
    class SessionStub(Session):
        pass

    def __init__(self, local_db: AgentDB):
        super().__init__(self.SessionStub())
        self._agents_by_uuid = local_db.entity_by_uuid
        self._agents_by_mail = local_db.entity_by_mail

    async def create(self, **kwargs) -> Agent:
        new_agent = Agent(id=str(uuid4()), **kwargs)
        self._agents_by_uuid[new_agent.id] = new_agent
        self._agents_by_mail[new_agent.email] = new_agent
        return new_agent

    async def get(self, uuid: str) -> Agent | None:
        if uuid in self._agents_by_uuid:
            return self._agents_by_uuid[uuid]
        return None

    async def get_agents_for_account(self, uuid: str) -> List[Agent]:
        result = []
        for elem in self._agents_by_uuid.values():
            if elem.account_id == uuid:
                result.append(elem)
        return result

    async def get_agent_by_email(self, email: str) -> Agent | None:
        if email in self._agents_by_mail:
            return self._agents_by_mail[email]
        return None

    async def get_all(self) -> List[Agent]:
        return list(self._agents_by_uuid.values())

    async def delete(self, uuid: str):
        if uuid in self._agents_by_uuid:
            del self._agents_by_uuid[uuid]

    async def update(self, uuid: str, **kwargs):
        new_agent = Agent(uuid, **kwargs)
        self._agents_by_uuid[new_agent.id] = new_agent
        self._agents_by_mail[new_agent.email] = new_agent
        return new_agent
