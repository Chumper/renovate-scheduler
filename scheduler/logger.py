import logging
import sys
import os

POD_NAME = os.environ.get("POD_NAME", "unknown")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = f"[%(asctime)s] {POD_NAME} %(name)-20.20s | %(levelname)-8.8s | %(message)s"

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, stream=sys.stdout)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
