from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from readability import Document
import requests
import logging
import colorlog
import weaviate
import os


def setup_weaviate_db() -> weaviate.Client:
    weaviate_api_key: Optional[str] = os.getenv("WEAVIATE_API_KEY")

    if weaviate_api_key is None:
        raise ValueError("WEAVIATE_API_KEY environment variable is not set.")

    auth_config = weaviate.AuthApiKey(api_key=weaviate_api_key)

    # Instantiate the client with the auth config
    client = weaviate.Client(
        url="https://localhost",
        auth_client_secret=auth_config,
    )

    return client


def setup_logger(name, log_level=logging.INFO) -> logging.Logger:
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
    paragraph_data = [p.get_text() for p in paragraphs]
    for pos, p in enumerate(paragraph_data):
        logger.debug(f"Added <p> tag {pos}: {p}")

    # TODO: Add something that parses tables
    # Extract text from <table> and addes it to a list with some formating
    # tables = soup.find_all("table")
    #
    # for table_pos, table in enumerate(tables):
    #     rows = table.find_all("tr")
    #     table_data = []
    #     for row in rows:
    #         cols = row.find_all(
    #             "td"
    #         )  # Change this to 'th' if you want to extract header cells
    #         cols = [col.get_text() for col in cols]
    #         table_data.append(cols)
    #     for row_pos, row in enumerate(table_data):
    #         logger.debug(f"Added row {row_pos} to table {table_pos}: {row}")

    return paragraph_data


def add_to_vector_db() -> None:
    """
    Addes data to vector database.
    """
    pass


def start() -> None:
    global logger
    load_dotenv()

    weaviate_client: weaviate.Client = setup_weaviate_db()
    logger: logging.Logger = setup_logger(__name__, logging.DEBUG)

    page = get_page(
        "https://catalog.stetson.edu/undergraduate/arts-sciences/computer-science/computer-science-bs/"
    )
    page_info = parse_html_for_vector_db(page)


# TODO: This will be removed at somepoint
if __name__ == "__main__":
    start()
