import requests
import logging
import openai
import os

from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from readability import Document
from datetime import datetime, timezone
from weaviate_handler import WeaviateHandler
from logger import setup_logger

logger = setup_logger(__name__)

def get_page(url):
    """
    Takes in a single URL and returns only relavent information from the page
    """
    try:
        logger.info(f"Requesting site: {url}")
        response = requests.get(url)

    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        raise

    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        raise

    else:
        logger.info(f"Site {url} receved, parsing text")

    doc = Document(response.text)

    if doc:
        logger.info(f"Found text on {url}")

        logger.debug(f"HTML from {url}:\n{doc.summary()}")
    else:
        logger.info(f"No text found on {url}")

    return doc


def parse_html_for_vector_db(html):
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

def add_webpage(site):
    # Getting info from webpage
    logger.info(f"Parsing HTML for {site}")
    webpage = get_page(site)
    current_time = datetime.now(timezone.utc)
    title = webpage.title()
    page_contents = parse_html_for_vector_db(webpage.summary())
    data = []

    # Putting webpage info in json format
    logger.info(f"Formating content for {site}")
    for content in page_contents:
        info = {
            "title": title,
            "url": site,
            "content": content,
        }
        data.append(info)

    # Batch adding data to Weaviate Database
    logger.info(f"Adding content to Weaviate database for {site}")
    weaviate.batch_add(data)



def gpt_stuff(content: str, role: str = "You are a helpful assistant.") -> dict:
    openai.api_key = os.getenv(
        "OPENAI_API_KEY"
    )  # TODO: Move OpenAI authenication somewhere else later

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": content},
        ],
    )

    return response


def start():
    setup_logger(__name__, logging.INFO)

    try:
        load_dotenv()

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
            ],
        }

        global weaviate
        weaviate = WeaviateHandler()
        # weaviate.add_schema(website)

        webpages = [
            "https://catalog.stetson.edu/undergraduate/arts-sciences/computer-science/computer-science-bs/",
            "https://www.stetson.edu/other/academics/undergraduate/education.php",
            "https://www.stetson.edu/law/academics/clinical-education/federal-litigation-internship.php",
        ]

        question: str = "What are the writing requirments to complete a degree in Computer Science degree?"

        for site in webpages:
            add_webpage(site)  # Assuming this is imported from the weaviate module

        response = weaviate.vector_search(
            "Webpage",
            [question],
            ["title", "content", "url"],
        )

        import json # TODO: Remember to remove this
        print(json.dumps(response, indent=2))

        role = "You are an admissions officer at Stetson univerisity. Using only the context provided, you will answer emailed questions."
        answer = response["data"]["Get"]["Webpage"][0]["content"]
        url = response["data"]["Get"]["Webpage"][0]["url"]

        content = f"Question: {question}\nAnswer: {answer} URL: {url}"

        print(gpt_stuff(content, role=role))

    except KeyboardInterrupt:
        logger.WARNING("Exiting program, have a nice day :)")

if __name__ == "__main__":
    start()
