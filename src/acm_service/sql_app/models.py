from sqlalchemy import Column, String
from acm_service.sql_app.database import Base


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    name = Column(String, index=False)

