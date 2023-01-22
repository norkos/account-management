from enum import Enum

from pydantic import BaseModel, EmailStr, UUID4

from acm_service.agents.schema import Agent


class RegionEnum(str, Enum):
    emea = 'emea'
    nam = 'nam'
    apac = 'apac'


class AccountBase(BaseModel):
    name: str
    email: EmailStr
    region: RegionEnum
    vip: bool


class AccountCreate(AccountBase):
    pass


class AccountWithoutAgents(AccountBase):
    id: UUID4

    class Config:
        orm_mode = True


class Account(AccountWithoutAgents):
    agents: list[Agent] = []

    class Config:
        orm_mode = True