"""Logger estructurado con niveles y formato configurable."""
import logging
import os
import sys


def get_logger(name: str = 'db-backup-notifier') -> logging.Logger:
    """Retorna logger configurado desde LOG_LEVEL env var."""
    level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s — %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )
    fmt.converter = __import__('time').gmtime
    handler.setFormatter(fmt)

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
