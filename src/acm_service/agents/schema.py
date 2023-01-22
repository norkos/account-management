from pydantic import BaseModel, EmailStr, UUID4


class AgentBase(BaseModel):
    name: str
    email: EmailStr


class AgentCreate(AgentBase):
    class Config:
        orm_mode = True


class Agent(AgentBase):
    id: UUID4
    account_id: UUID4
    blocked: bool

    class Config:
        orm_mode = True