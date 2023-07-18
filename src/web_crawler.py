from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from readability import Document
import requests
import logging
import colorlog
import weaviate
import os


def setup_logger(name, log_level=logging.INFO) -> None:
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


def setup_weaviate_db() -> None:
    logger.info("Setting up Weaviate Client")
    global weaviate_client

    weaviate_api_key: Optional[str] = os.getenv("WEAVIATE_API_KEY")
    weaviate_url: Optional[str] = os.getenv("WEAVIATE_URL")

    logger.info("Checking if API Keys exist")

    if weaviate_api_key is None:
        error_message: str = "WEAVIATE_API_KEY environment variable is not set."
        logger.error(error_message)
        raise ValueError(error_message)

    if weaviate_url is None:
        error_message: str = "WEAVIATE_URL environment variable is not set."
        logger.error(error_message)
        raise ValueError(error_message)

    logger.info("API Keys exist, connecting to database")

    auth_config: weaviate.AuthApiKey = weaviate.AuthApiKey(api_key=weaviate_api_key)

    # Instantiate the client with the auth config
    weaviate_client = weaviate.Client(
        url=weaviate_url,
        auth_client_secret=auth_config,
    )

    logger.info("Connected to Weaviate database")

    website = {
        "class": "Webpage",
        "description": "A webpage from a website specified in the whitelist",
        "vectorizer": "text2vec-transformers",
        "properties": [
            {
                "name": "title",
                "description": "The title of the webpage",
                "datatype": ["text"],
            },
            {
                "name": "url",
                "description": "The url of the webpage",
                "datatype": ["text"],
            },
            {
                "name": "section",
                "description": "The section of the webpage",
                "datatype": ["text"],
            },
            {
                "name": "content",
                "description": "The content of the webpage",
                "datatype": ["text"],
            },
            {
                "name": "last-updated",
                "description": "The date when this entry was last modified",
                "datatype": ["date"],
            },
        ],
    }

    weaviate_client.schema.create_class(website)


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
        # TODO: Should this be logged?
        logger.debug(f"HTML from {url}:\n{doc.summary()}")
    else:
        logger.info(f"No text found on {url}")

    return doc.summary()


def parse_html_for_vector_db(html: str) -> list[str]:
    """
    Takes in HTML input and returns an array of strings.
    """
    logger.info(f"Parsing HTML")
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")

    # Extract text from each <p> tag and add it to a list
    paragraph_data = [p.get_text() for p in paragraphs if p.get_text().strip()]
    for pos, p in enumerate(paragraph_data):
        logger.debug(f"Added <p> tag {pos}: {p}")

    # TODO: Add something that parses tables

    return paragraph_data


def add_to_vector_db(items: list[str]) -> None:
    """
    Addes data to vector database.
    """
    logger.info("Adding items to Weaviate database")


def start() -> None:
    load_dotenv()

    setup_logger(__name__, logging.INFO)
    setup_weaviate_db()

    page = get_page(
        "https://catalog.stetson.edu/undergraduate/arts-sciences/computer-science/computer-science-bs/"
    )
    page_info = parse_html_for_vector_db(page)
    add_to_vector_db(page_info)


# TODO: This will be removed at somepoint
if __name__ == "__main__":
    start()
