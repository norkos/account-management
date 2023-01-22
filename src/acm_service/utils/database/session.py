import logging
from contextlib import asynccontextmanager

from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import AsyncAdaptedQueuePool

from acm_service.utils.env import ASYNC_DB_URL
from acm_service.utils.logconf import DEFAULT_LOGGER

logger = logging.getLogger(DEFAULT_LOGGER)

engine = create_async_engine(ASYNC_DB_URL, future=True, echo=False, pool_size=20, max_overflow=10,
                             poolclass=AsyncAdaptedQueuePool)


async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession, autocommit=False, autoflush=False)


@asynccontextmanager
async def create_session() -> AsyncSession:
    async with async_session() as session:
        yield session


Base = declarative_base()
