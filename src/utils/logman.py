import logging
from logging import handlers
from pathlib import Path

# TODO: Remove this
debug = True


parent_dir = Path(__file__).parent
log_file = parent_dir.parent.joinpath("logs").joinpath("vuln.log")

if not log_file.parent.exists():
    log_file.parent.mkdir()

# TODO (Shubham): change format to JSON for kafka purpose
logger = logging.getLogger(__name__)
fmt = "%(asctime)s %(name)s [%(levelname)s] %(module)s.%(funcName)s -> %(message)s"
formatter = logging.Formatter(fmt=fmt)
logger.setLevel(level=logging.INFO)

file_handler = handlers.RotatingFileHandler(
    filename=str(log_file).split(".")[-2] + ".log",
    mode="a",
    maxBytes=3 * 1024 * 1024,
    backupCount=10,
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


if debug:
    std_handler = logging.StreamHandler()
    std_handler.setFormatter(formatter)
    logger.addHandler(std_handler)
