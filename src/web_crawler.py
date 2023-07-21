from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from readability import Document
from datetime import datetime, timezone
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

    # TODO: Check if there is a better way to write this 
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

    # TODO: figure out how to check if the class is already made 
    website = {
        "class": "Webpage",
        "description": "A webpage from a website specified in the whitelist",
        "vectorizer": "text2vec-transformers",
        "properties": [
            {
                "name": "title",
                "description": "The title of the webpage",
                "dataType": ["text"],
            },
            {
                "name": "url",
                "description": "The url of the webpage",
                "dataType": ["text"],
            },
            {
                "name": "content",
                "description": "The content of the webpage",
                "dataType": ["text"],
            },
            # TODO: This is probally redundent, Weaviate keeps track of this already
            {
                "name": "last_updated",
                "description": "The date when this entry was last modified",
                "dataType": ["date"],
            },
        ],
    }

    # weaviate_client.schema.create_class(website) 


def get_page(url: str) -> Document:
    """
    Takes in a single URL and returns only relavent information from the page
    """
    try:
        logger.info(f"Requesting site: {url}")
        response = requests.get(url)

    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return

    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return
    else:
        logger.info(f"Site {url} receved, parsing text")

    doc: Document = Document(response.text)

    if doc:
        logger.info(f"Found text on {url}")
        
        logger.debug(f"HTML from {url}:\n{doc.summary()}")
    else:
        logger.info(f"No text found on {url}")

    return doc


def parse_html_for_vector_db(html: str) -> list[str]:
    """
    Takes in HTML input and returns an array of strings.
    """
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")

    # Extract text from each <p> tag and add it to a list
    # TODO: Make this more readable 
    paragraph_data = [p.get_text() for p in paragraphs if p.get_text().strip()]
    for pos, p in enumerate(paragraph_data):
        logger.debug(f"Added <p> tag {pos}: {p}")

    # TODO: Add something that parses tables

    return paragraph_data

def add_webpage_to_db(site: str) -> bool:
    # Getting info from webpage
    logger.info(f'Parsing HTML for {site}')
    webpage: Document = get_page(site)
    current_time: datetime = datetime.now(timezone.utc)
    title: str = webpage.title()
    page_contents: list[str] = parse_html_for_vector_db(webpage.summary())
    data: list[dict[str, str]] = []

    # Putting webpage info in json format
    logger.info(f'Formating content for {site}')
    for content in page_contents:
        info: dict[str, str] = {
                    'title': title,
                    'url': site, 
                    # 'section': section # TODO: Code in section
                    'content': content,
                    'last_updated': current_time.isoformat()
                }
        data.append(info)

    # Batch adding data to Weaviate Database
    logger.info(f'Adding content to Weaviate database for {site}')
    with weaviate_client.batch as batch:
        batch.batch_size = 100

        for i, d in enumerate(data):
            logger.debug(f'Adding the following to Weaviate Database:\n{d}')
            properties = {
                    'title': d['title'],
                    'url': d['url'], 
                    # 'section': section # TODO: Code in section
                    'content': d['content'],
                    'last_updated': d['last_updated']
                    }
            weaviate_client.batch.add_data_object(properties, "Webpage")
    logger.debug(f'Content added to Weaviate database for {site}')

    return True # TODO: make this return false if getting the webpage fails


def start() -> None:
    try: 
        load_dotenv()


        setup_logger(__name__, logging.DEBUG)
        setup_weaviate_db()
        webpages = [
                    "https://catalog.stetson.edu/undergraduate/arts-sciences/computer-science/computer-science-bs/",
                    "https://www.stetson.edu/other/academics/undergraduate/education.php"
                    "https://www.stetson.edu/law/academics/clinical-education/federal-litigation-internship.php"
                ] 

        for site in webpages:
            add_webpage_to_db(site)

        import json
        print(
                json.dumps(
                    weaviate_client.data_object.get(),
                    indent = 2
                    )
                )
    except KeyboardInterrupt:
        logger.WARNING('Exiting program, have a nice day :)')


# TODO: This will be removed at somepoint
if __name__ == "__main__":
    start()
