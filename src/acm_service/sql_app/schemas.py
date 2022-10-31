from pydantic import BaseModel, EmailStr, UUID4


class AccountBase(BaseModel):
    name: str
    email: EmailStr


class AccountCreate(AccountBase):
    pass


class AccountInDB(AccountBase):
    id: UUID4

    class Config:
        orm_mode = True
        allow_mutation = False  # can't touch this, la la la
