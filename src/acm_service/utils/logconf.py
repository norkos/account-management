from acm_service.utils.env import DEBUG_LOGGER_LEVEL

DEFAULT_LOGGER = 'DEFAULT'

log_config = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s | %(levelname)s | %(pathname)s:%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "database": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s.%(msecs)03d Database | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "database": {
            "formatter": "database",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        }
    },
    "loggers": {
        DEFAULT_LOGGER: {"handlers": ["default"],
                         "level": "DEBUG" if DEBUG_LOGGER_LEVEL else "INFO", "propagate": False},
        "sqlalchemy.engine":  {"handlers": ["database"],
                               "level": "DEBUG" if DEBUG_LOGGER_LEVEL else "WARNING", "propagate": False}
    },
}