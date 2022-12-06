from pydantic import BaseModel, EmailStr, UUID4
from enum import Enum

class AgentBase(BaseModel):
    name: str
    email: EmailStr


class AgentCreate(AgentBase):
    pass


class Agent(AgentBase):
    id: UUID4
    account_id: str

    class Config:
        orm_mode = True


class RegionEnum(str, Enum):
    emea = 'emea'
    nam = 'nam'
    apac = 'apac'


class AccountBase(BaseModel):
    name: str
    email: EmailStr
    region: RegionEnum


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
