import logging
from rich.logging import RichHandler
import os

LOG_DIR = "logs"
DEFAULT_FILE_LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)


def setup_logger(log_name=None, log_level=logging.INFO, log_file_name=None):
    """
    Setup and return a logger with given parameters.

    Parameters:
    - logger_name: Name of the logger.
    - log_level: Level of logging like logging.DEBUG, logging.INFO, etc.
    - log_file_name: Name of the file to log to. If None, only console logging is set up.

    Returns:
    - Configured logger object.
    """
    # Ensure logging directory exists
    if log_file_name and not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    logger.propagate = False

    # Check if handlers already exist before adding new ones
    if not logger.hasHandlers():
        # Set up the file logging handler if log_file_name is provided
        if log_file_name:
            file_formatter = logging.Formatter(DEFAULT_FILE_LOG_FORMAT)
            file_handler = logging.FileHandler(os.path.join(LOG_DIR, log_file_name))
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Set up the console logging handler using rich's RichHandler
        rich_handler = RichHandler(rich_tracebacks=True)
        rich_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(rich_handler)

    return logger
