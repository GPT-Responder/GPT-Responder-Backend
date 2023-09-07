import logging
import colorlog


def setup_logger(name, log_level=logging.INFO):
    """
    Sets up the logger
    """
    global logger
    # Define log colors
    log_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }

    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False

    # Create console handler
    ch: logging.StreamHandler = logging.StreamHandler()
    ch.setLevel(log_level)

    # Create formatter and add it to the handlers
    formatter: colorlog.ColoredFormatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(levelname)s] [%(asctime)s] - %(message)s",
        datefmt=None,
        reset=True,
        log_colors=log_colors,
        secondary_log_colors={},
        style="%",
    )

    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)

    return logger
