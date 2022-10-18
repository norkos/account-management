from pydantic import BaseModel


class AccountBase(BaseModel):
    name: str | None = None
    email: str | None = None


class AccountCreate(AccountBase):
    pass


#class Account(AccountBase):
#    id: str
#
#    class Config:
#        orm_mode = True
