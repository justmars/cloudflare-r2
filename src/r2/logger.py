import logging
import sys
from pathlib import Path

LOG_FILE = Path().cwd() / "app.log"


# See setup https://subsid.github.io/posts/2023-03-06-python-logging/
def remove_handlers():
    logger = logging.getLogger()
    for h in list(logger.handlers):
        logger.removeHandler(h)


def setup_logging(level="INFO"):
    ## Reset logger
    remove_handlers()

    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")

    consoleh = logging.StreamHandler(sys.stdout)

    def nonerror(record):
        return record.levelno != logging.ERROR

    def error(record):
        return record.levelno == logging.ERROR

    errorh = logging.StreamHandler(sys.stderr)
    errorh.setLevel(logging.ERROR)
    errorh.setFormatter(formatter)

    consoleh.setFormatter(formatter)
    consoleh.addFilter(nonerror)
    errorh.addFilter(error)

    logger.addHandler(consoleh)
    logger.addHandler(errorh)
    logger.setLevel(level)


def file_logging(level="INFO"):
    ## Reset logger
    remove_handlers()

    logger = logging.getLogger()
    fh = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(level)


if not LOG_FILE.exists():
    file_logging()
