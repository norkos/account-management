from sqlalchemy import Column, String, ForeignKey
from acm_service.sql_app.database import Base
from sqlalchemy.orm import relationship


class Agent(Base):
    __tablename__ = 'agents'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    name = Column(String, index=False)

    account_id = Column(String, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    name = Column(String, index=False)
    region = Column(String, nullable=False)

    agents = relationship('Agent',  cascade='all,delete', backref='accounts', passive_deletes=True)
