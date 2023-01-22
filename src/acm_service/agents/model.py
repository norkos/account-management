from sqlalchemy import Column, String, Boolean, ForeignKey

from acm_service.utils.database.session import Base


class Agent(Base):
    __tablename__ = 'agents'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    name = Column(String, index=False)
    blocked = Column(Boolean, default=False, nullable=False)

    account_id = Column(String, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)