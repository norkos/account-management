from uuid import uuid4
from typing import List

import namegenerator
from aio_pika.abc import AbstractRobustConnection
from pydantic import EmailStr

from acm_service.data_base.repositories import AccountRepository, AbstractRepository
from acm_service.events.producer import EventProducer
from acm_service.data_base.schemas import Account, Agent, RegionEnum


def generate_random_mail() -> str:
    return f'{namegenerator.gen()}@gmail.com'


class RabbitProducerStub(EventProducer):

    def attach_to_connection(self, event_broker: AbstractRobustConnection | None):
        pass

    async def block_agent(self, region: str, agent_uuid: str) -> None:
        pass

    async def unblock_agent(self, region: str, agent_uuid: str) -> None:
        pass

    async def create_agent(self, region: str, agent_uuid: str) -> None:
        pass

    async def delete_agent(self, region: str, agent_uuid: str) -> None:
        pass

    async def create_account(self, region: str, account_uuid: str, vip: bool) -> None:
        pass

    async def delete_account(self, region: str, account_uuid: str, vip: bool) -> None:
        pass


class AccountRepositoryStub(AbstractRepository):

    def __init__(self):
        super().__init__()
        self._accounts_by_uuid = {}
        self._accounts_by_mail = {}

    def create_random(self) -> Account:
        new_account = Account(id=uuid4(), name='dummy_name', email=EmailStr(generate_random_mail()),
                              region=RegionEnum.emea, vip=False)
        self._accounts_by_uuid[new_account.id] = new_account
        self._accounts_by_mail[new_account.email] = new_account
        return new_account

    async def create(self, **kwargs) -> Account:
        new_account = Account(id=uuid4(), **kwargs)
        self._accounts_by_uuid[new_account.id] = new_account
        self._accounts_by_mail[new_account.email] = new_account
        return new_account

    async def get(self, account_uuid: str) -> Account | None:
        if account_uuid in self._accounts_by_uuid:
            return self._accounts_by_uuid[account_uuid]
        return None

    async def get_by(self, **kwargs) -> List[Account]:
        if 'email' in kwargs.keys():
            return self.get_account_by_email(kwargs['email'])

        raise NotImplementedError

    def get_account_by_email(self, email: str) -> List[Account]:
        if email in self._accounts_by_mail:
            return [self._accounts_by_mail[email]]
        return []

    async def get_all(self) -> List[Account]:
        return list(self._accounts_by_uuid.values())

    async def delete(self, account_uuid: str) -> None:
        if account_uuid in self._accounts_by_uuid:
            del self._accounts_by_uuid[account_uuid]

    async def update(self, account_uuid: str, **kwargs) -> None:
        agent = self._accounts_by_uuid[account_uuid]
        for k in kwargs.keys():
            agent.__setattr__(k, kwargs[k])

    async def delete_all(self) -> None:
        self._accounts_by_uuid = {}
        self._accounts_by_mail = {}


class AgentRepositoryStub(AbstractRepository):

    def __init__(self):
        super().__init__()
        self._agents_by_uuid = {}
        self._agents_by_mail = {}

    async def create(self, **kwargs) -> Agent:
        new_agent = Agent(id=uuid4(), **kwargs)
        self._agents_by_uuid[new_agent.id] = new_agent
        self._agents_by_mail[new_agent.email] = new_agent
        return new_agent

    async def get(self, agent_uuid: str) -> Agent | None:
        if agent_uuid in self._agents_by_uuid:
            return self._agents_by_uuid[agent_uuid]
        return None

    async def get_by(self, **kwargs) -> List[Agent]:
        if 'email' in kwargs.keys():
            return self.get_agent_for_email(kwargs['email'])

        if 'account_id' in kwargs.keys():
            return self.get_agents_for_account(kwargs['account_id'])

        raise NotImplementedError

    def get_agent_for_email(self, email: str) -> List[Agent]:
        if email in self._agents_by_mail.keys():
            return [self._agents_by_mail[email]]
        return []

    def get_agents_for_account(self, agent_uuid: str) -> List[Agent]:
        result = []
        for elem in self._agents_by_uuid.values():
            if elem.account_id == agent_uuid:
                result.append(elem)
        return result

    async def get_all(self) -> List[Agent]:
        return list(self._agents_by_uuid.values())

    async def delete(self, agent_uuid: str):
        if agent_uuid in self._agents_by_uuid:
            del self._agents_by_uuid[agent_uuid]

    async def update(self, agent_uuid: str, **kwargs):
        agent = self._agents_by_uuid[agent_uuid]
        for k in kwargs.keys():
            agent.__setattr__(k, kwargs[k])

    async def delete_all(self):
        self._agents_by_uuid = {}
        self._agents_by_mail = {}
