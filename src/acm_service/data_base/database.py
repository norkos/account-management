from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import AsyncAdaptedQueuePool

from acm_service.utils.env import ASYNC_DB_URL

engine = create_async_engine(ASYNC_DB_URL, future=True, echo=False, pool_size=20,
                             max_overflow=10, poolclass=AsyncAdaptedQueuePool)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession, autocommit=False, autoflush=False)

Base = declarative_base()
