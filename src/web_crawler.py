import html2text
import scrapy
import openai
import os

from dotenv import load_dotenv
from rich import print
from logger_setup import setup_logger
from readability import Document
from weaviate_handler import WeaviateHandler
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

logger = setup_logger(logger_name=__name__)


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
        self.blacklisted_domains = kwargs.get("blacklisted_domains", [])

    def parse(self, response):
        page_title = response.xpath("//title/text()").get()
        logger.info(f"Getting HTML for URL: {response.url}")

        # Extract content from the current page
        if response.text is None:
            logger.warning(f"No content found in URL: {response.url}")
        else:
            add_webpage(page_title, response.url, response.text)

        # Follow links to other pages within the allowed domains
        for href in response.css("a::attr(href)").extract():
            # Check if the URL is blacklisted
            if any(blacklist in href for blacklist in self.blacklisted_domains):
                logger.debug(f"Skipping blacklisted link: {href}")
                continue

            logger.debug(f"Following link: {href}")
            yield response.follow(href, self.parse)


def add_webpage(title, url, html_content):
    """
    Adds the given webpage content (associated with a URL) to the database.
    """
    doc = Document(html_content)

    text_converter = html2text.HTML2Text()
    text_converter.ignore_links = True
    content = text_converter.handle(doc.summary())

    data = []

    # Putting webpage info in JSON format
    logger.info(f"Formating content for {url}")
    info = {
        "title": title,
        "url": url,
        "content": content,
    }
    data.append(info)

    # Batch adding data to Weaviate Database
    logger.info(f"Adding content to Weaviate database for {url}")
    weaviate.batch_add(data)


def gpt_stuff(content, role = "You are a helpful assistant."):
    logger.info("Authenicating with OpenAI")
    openai.api_key = os.getenv(
        "OPENAI_API_KEY"
    )  # TODO: Move OpenAI authenication somewhere else later

    logger.info("Asking GPT 3.5-turbo")
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

        start_urls = ["https://stetson.edu", "https://catalog.stetson.edu/"]
        allowed_urls = ["stetson.edu"]
        blacklist_urls = ["kaltura.stetson.edu", "stetson.edu/search/"]
        process = CrawlerProcess(get_project_settings())
        process.crawl(
            WebpageSpider,
            start_urls=start_urls,
            allowed_domains=allowed_urls,
            blacklisted_domains=blacklist_urls,
        )
        # process.start()

        while True:
            question = input("Question to ask Weaviate (enter q to quit): ")
            if question == "q":
                break
            response = weaviate.vector_search(
                "Webpage",
                [question],
                ["title", "content", "url"],
            )

            role = "You are an admissions officer at Stetson univerisity. Using only the context provided, you will answer emailed questions. Do not add an email signature."
            answer = response["data"]["Get"]["Webpage"][0]["content"]
            url = response["data"]["Get"]["Webpage"][0]["url"]
            title = response["data"]["Get"]["Webpage"][0]["title"]

            content = f"Question: {question}\nAnswer: {answer} URL: {url}"
            gpt_response = gpt_stuff(content, role=role)["choices"][0]["message"][
                "content"
            ]

            print("[blue]Role[/blue]:", role)
            print("[blue]Question:[/blue]", question)
            print(
                "[blue]Database Answer:[/blue]",
                f"[green]{title}[/green] -",
                url,
                "\n",
                answer,
            )
            print("[blue]GPT Response:[/blue]", gpt_response)

    except KeyboardInterrupt:
        logger.warning("Exiting program, have a nice day :)")
