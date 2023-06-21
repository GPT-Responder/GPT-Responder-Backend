from bs4 import BeautifulSoup
import requests
import logging, colorlog

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(levelname)s] [%(asctime)s] - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
    secondary_log_colors={},
    style="%",
)

ch.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(ch)


def get_page(url):
    logging.info(f"Requesting page: {url}")
    page = requests.get(url)
    doc = BeautifulSoup(page.text, "html.parser")

    article = doc.article

    return article


if __name__ == "__main__":
    page = get_page(
        "https://www.stetson.edu/administration/information-technology/help-desk/"
    )
