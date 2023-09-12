import requests
import scrapy
import logging
import openai
import os

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from logger_setup import setup_logger
from readability import Document
from datetime import datetime, timezone
from weaviate_handler import WeaviateHandler
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

logger = setup_logger(logger_name=__name__, log_level=logging.DEBUG)


class WebpageSpider(scrapy.Spider):
    name = "webpage_spider"

    custom_settings = {
        "LOG_ENABLED": False,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 5,
        "AUTOTHROTTLE_MAX_DELAY": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
    }

    def __init__(self, *args, **kwargs):
        super(WebpageSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs.get("start_urls")
        self.allowed_domains = kwargs.get("allowed_domains", [])

    def parse(self, response):
        # Logging the URL being processed.
        logger.info(f"Processing URL: {response.url}")

        # Extract content from the current page
        page_contents = parse_html_for_vector_db(response.text)
        if not page_contents:
            logger.warning(f"No content found in URL: {response.url}")

        for content in page_contents:
            print("RESPONSE URL:", response.url)
            add_webpage(response.url, content)

        # Follow links to other pages within the allowed domains
        for href in response.css("a::attr(href)").extract():
            logger.debug(f"Following link: {href}")
            yield response.follow(href, self.parse)


def parse_html_for_vector_db(html):
    """
    Takes in HTML input and returns an array of strings.
    """
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")

    # Extract text from each <p> tag and add it to a list
    paragraph_data = [p.get_text() for p in paragraphs if p.get_text().strip()]
    for pos, p in enumerate(paragraph_data):
        logger.debug(f"Added <p> tag {pos}: {p}")

    if paragraph_data:
        logger.info(f"Parsed HTML and extracted {len(paragraph_data)} paragraphs.")
    else:
        logger.warning(f"No text content found in the provided HTML.")

    # TODO: Add something that parses tables

    return paragraph_data


def add_webpage(url, html_content):
    """
    Adds the given webpage content (associated with a URL) to the database.
    """
    logger.info(f"Processing webpage: {url}")

    doc = Document(html_content)
    current_time = datetime.now(timezone.utc)
    title = doc.title()
    data = []

    if title:
        logger.info(f"Extracted title: {title}")
    else:
        logger.warning(f"Couldn't extract a title for {url}")

    page_contents = parse_html_for_vector_db(doc.summary())

    # Putting webpage info in JSON format
    logger.info(f"Formating content for {url}")
    for content in page_contents:
        info = {
            "title": title,
            "url": url,
            "content": content,
        }
        data.append(info)

    # Batch adding data to Weaviate Database
    logger.info(f"Adding content to Weaviate database for {url}")
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


if __name__ == "__main__":
    try:
        load_dotenv()

        # TODO: Add a deterministic ID to prevent duplicates
        # https://weaviate.io/developers/weaviate/manage-data/create#preventing-duplicates
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

        start_urls = ["https://stetson.edu"]
        allowed_urls = ["stetson.edu"]
        process = CrawlerProcess(get_project_settings())
        process.crawl(
            WebpageSpider, start_urls=start_urls, allowed_domains=allowed_urls
        )
        process.start()

        question = "What are the major requirments for csci?"
        response = weaviate.vector_search(
            "Webpage",
            [question],
            ["title", "content", "url"],
        )

        # role = "You are an admissions officer at Stetson univerisity. Using only the context provided, you will answer emailed questions."
        # answer = response["data"]["Get"]["Webpage"][0]["content"]
        # url = response["data"]["Get"]["Webpage"][0]["url"]
        #
        # content = f"Question: {question}\nAnswer: {answer} URL: {url}"
        #
        # print(gpt_stuff(content, role=role))

    except KeyboardInterrupt:
        logger.warning("Exiting program, have a nice day :)")
