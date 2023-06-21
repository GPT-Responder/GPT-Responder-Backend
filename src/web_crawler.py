from bs4 import BeautifulSoup
import requests
import logging
import colorlog


def setup_logger(name, log_level=logging.DEBUG, stream_handler_level=logging.DEBUG):
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

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(stream_handler_level)

    # Create formatter and add it to the handlers
    formatter = colorlog.ColoredFormatter(
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


def get_page(url):
    # TODO: Set up exception handeling
    logger.info(f"Requesting page: {url}")
    page = requests.get(url)
    doc = BeautifulSoup(page.text, "html.parser")
    article = doc.article

    return article


def start():
    global logger

    logger = setup_logger(__name__)


if __name__ == "__main__":
    start()
    page = get_page(
        "https://www.stetson.edu/administration/information-technology/help-desk/"
    )
