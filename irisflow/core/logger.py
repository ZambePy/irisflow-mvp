"""Logger centralizado do IrisFlow."""
import logging
import sys


def setup_logger(name: str = "irisflow", level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s — %(message)s",
                          datefmt="%H:%M:%S")
    )
    logger.addHandler(handler)
    return logger


logger = setup_logger()
