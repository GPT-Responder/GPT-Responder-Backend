from typing import Optional
from bs4 import BeautifulSoup
from readability import Document
import requests
import logging
import colorlog


def setup_logger(name, log_level=logging.DEBUG):
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
    ch.setLevel(log_level)

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


def get_page(url: str) -> Optional[str]:
    """
    Takes in a single URL and returns only relavent information from the page
    """
    try:
        logger.info(f"Requesting site: {url}")
        response = requests.get(url)

    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return None

    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return None
    else:
        logger.info(f"Site {url} receved, parsing text")

    doc: Document = Document(response.text)

    if doc:
        logger.info(f"Found text on {url}")
        logger.debug(doc.summary)
    else:
        logger.info(f"No text found on {url}")

    return doc.summary()


def parse_html_for_vector_db(html: str) -> list[str]:
    """
    Takes in HTML input and returns a list of strings spilit up to be used
    in a vector database.
    """
    pass


def add_to_vector_db() -> None:
    """
    Addes data to vector database.
    """
    pass


def start() -> None:
    global logger

    logger = setup_logger(__name__)
    print(get_page("https://www.stetson.edu/other/about/history.php"))


if __name__ == "__main__":
    start()
