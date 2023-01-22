import abc
import logging

from acm_service.utils.logconf import DEFAULT_LOGGER

logger = logging.getLogger(DEFAULT_LOGGER)


def log_exception(coro):
    async def wrap(*args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except BaseException as exc:
            logger.exception("Exception %s", exc)
            raise exc

    return wrap


class AbstractRepository(abc.ABC):
    async def get(self, reference):
        raise NotImplementedError

    async def get_by(self, **kwargs):
        raise NotImplementedError

    async def get_all(self):
        raise NotImplementedError

    async def create(self, **kwargs):
        raise NotImplementedError

    async def delete(self, reference):
        raise NotImplementedError

    async def delete_all(self):
        raise NotImplementedError

    async def update(self, reference, **kwargs):
        raise NotImplementedError
