from pydantic import BaseModel


class AccountBase(BaseModel):
    name: str | None = None
    email: str | None = None


class AccountCreate(AccountBase):
    pass


class AccountInDB(AccountBase):
    id: str

    class Config:
        orm_mode = True
        allow_mutation = False #can't touch this, la la la
