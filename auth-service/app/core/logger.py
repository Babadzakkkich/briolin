import sys
import logging
from app.core.config import settings

def get_logger(name: str):
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    logger.propagate = False 

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = get_logger("briolin.auth")