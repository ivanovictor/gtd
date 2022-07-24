"""Custom logger."""
from sys import stdout
from loguru import logger


def create_logger():
    """Create custom logger."""
    logger.remove()
    logger.add(
        stdout,
        level="DEBUG",
    )
    return logger


logger = create_logger()
