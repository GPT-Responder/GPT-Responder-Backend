from bs4 import BeautifulSoup
from readability import Document
import requests
import logging
import colorlog


def setup_logger(name, log_level=logging.DEBUG, stream_handler_level=logging.DEBUG):
    """
    Sets up the logger
    """
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
    """
    Takes in a single URL and returns only relavent information from the page
    """
    try:
        logger.info(f"Requesting site: {url}")
        response = requests.get(url)

    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")  # Python 3.6
        return None

    except Exception as err:
        logger.error(f"Other error occurred: {err}")  # Python 3.6
        return None

    doc = Document(response.text)

    return doc.summary()


def start():
    global logger

    logger = setup_logger(__name__)


if __name__ == "__main__":
    start()
    # get_page(
    #     "https://catalog.stetson.edu/undergraduate/arts-sciences/computer-science/cyber-security-bs/#text"
    # )
    # print("\n----------------------------------------------------\n")
    get_page("https://www.stetson.edu/administration/information-technology/help-desk/")
