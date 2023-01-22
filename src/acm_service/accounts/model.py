from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from acm_service.utils.database.session import Base


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    name = Column(String, index=False)
    region = Column(String, nullable=False)
    vip = Column(Boolean, nullable=False)

    agents = relationship('Agent',  cascade='all,delete', backref='accounts', passive_deletes=True)