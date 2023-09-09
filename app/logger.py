import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
print(LOG_LEVEL)
handler = logging.StreamHandler()
handler.setLevel(LOG_LEVEL)
formatter = logging.Formatter(fmt="%(levelname)s:%(name)s:%(message)s")
handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger_db_client = logging.getLogger("db_client")
logger_db_client.setLevel(LOG_LEVEL)
logger_db_client.addHandler(handler)

logger_tortoise = logging.getLogger("tortoise")
logger_tortoise.setLevel(LOG_LEVEL)
logger_tortoise.addHandler(handler)
