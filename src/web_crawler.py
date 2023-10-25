import html2text
import scrapy
import threading

from chat_gpt import ChatGPT
from dotenv import load_dotenv
from logger_setup import setup_logger
from readability import Document
from rich import print
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from weaviate_handler import WeaviateHandler

logger = setup_logger()


class WebpageSpider(scrapy.Spider):
    name = "webpage_spider"

    custom_settings = {
        "LOG_LEVEL": "WARNING",
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
            threading.Thread(target=add_webpage, args=(page_title, response.url, response.text)).start()
            # add_webpage(page_title, response.url, response.text)

        # Follow links to other pages within the allowed domains
        for href in response.css("a::attr(href)").extract():
            # Convert relative URLs to absolute URLs
            absolute_url = response.urljoin(href)

            # Check if the URL is blacklisted
            if any(blacklist.lower() in absolute_url.lower() for blacklist in self.blacklisted_domains):
                logger.info(f"Skipping blacklisted link: {absolute_url}")
                continue

            logger.debug(f"Following link: {href}")
            yield response.follow(href, self.parse)


def add_webpage(title, url, html_content, token_skip=50):
    """
    Adds the given webpage content (associated with a URL) to the database.
    """
    doc = Document(html_content)

    text_converter = html2text.HTML2Text()
    text_converter.ignore_images = True
    text_converter.body_width = 0
    content = text_converter.handle(doc.summary())

    chatgpt = ChatGPT()
    content_tokens = chatgpt.string_to_tokens(content)
    if content_tokens < token_skip:
        logger.warning(f"Skipping {url} because it has less than {token_skip} tokens")
        return

    role = 'I want you to act as a Website Content Analyst - FAQ Specialist, analyze the client webpage below to identify 10 common questions from visitors. List each question on a new line without numbering or bullet-pointing.'
    prompt = '' + content
    token_count = chatgpt.string_to_tokens(prompt)

    if token_count > 4096:
        logger.warning(f"Prompt is too long ({token_count} tokens), using 16k model instead")
        gpt_response = chatgpt.prompt(prompt, role, model="gpt-3.5-turbo-16k")
    else:
        gpt_response = chatgpt.prompt(prompt, role)

    most_common_questions = gpt_response['choices'][0]['message']['content']
    most_common_questions = most_common_questions.split('\n')
    logger.debug(f'GPT Response: {gpt_response}')


    # TODO: If chatgpt returns a response like "Sorry, I don't have enough information" then most_common_questions should be None

    # TODO: Make this level debug later
    logger.debug(f"Most common questions for {url}:\n{most_common_questions}")

    # Putting webpage info in JSON format
    logger.info(f"Formating content for {url}")
    data = {
        "title": title,
        "url": url,
        "content": content,
        "mostCommonQuestions": most_common_questions,
    }

    # Batch adding data to Weaviate Database
    logger.info(f"Adding content to Weaviate database for {url}")
    weaviate.add(data, url)


if __name__ == "__main__":
    try:
        load_dotenv()

        # TODO: Add a deterministic ID to prevent duplicates
        # https://weaviate.io/developers/weaviate/manage-data/create#preventing-duplicates
        website = {
            "class": "Webpage",
            "description": "A webpage from a website specified in the whitelist",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                "model": "ada",
                "modelVersion": "002",
                "type": "text",
                "baseURL": "https://api.openai.com",
                }
            },
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
                {
                    "name": "mostCommonQuestions",
                    "description": "The most common questions asked about the webpage",
                    "dataType": ["text[]"],
                },
            ],
        }

        global weaviate
        weaviate = WeaviateHandler()
        weaviate.add_schema(website)

        start_urls = ["https://stetson.edu", "https://catalog.stetson.edu/"]
        allowed_urls = ["stetson.edu"]
        with open('config/url_blocklist.txt') as f:
            blocklist_urls = f.readlines()

        blocklist_urls = [x.strip() for x in blocklist_urls] 
        process = CrawlerProcess(get_project_settings())
        process.crawl(
            WebpageSpider,
            start_urls=start_urls,
            allowed_domains=allowed_urls,
            blacklisted_domains=blocklist_urls,
        )
        process.start()

        # while True:
        #     question = input("Question to ask Weaviate (enter q to quit): ")
        #     if question == "q":
        #         break
        #     response = weaviate.vector_search(
        #         "Webpage",
        #         question,
        #         ["title", "content", "url"],
        #         hybrid_properties=["mostCommonQuestions^3", "content", 'title^5'],
        #     )
        #
        #
        #     print(response)
        #
        #     role = "You are an admissions officer at Stetson univerisity. Using only the context provided, you will answer emailed questions. Do not add an email signature. Make sure to always include the webpage link."
        #     webpage_data = response["data"]["Get"]["Webpage"][0]
        #     context = webpage_data["content"]
        #     url = webpage_data["url"]
        #     title = webpage_data["title"]
        #
        #     chatgpt = ChatGPT()
        #
        #     content = f"Question: {question}\nContext: {context} URL: {url}"
        #     gpt_response = chatgpt.prompt(content, role=role)["choices"][0]["message"]["content"]
        #
        #     print("[blue]Role[/blue]:", role)
        #     print("[blue]Question:[/blue]", question)
        #     print(
        #         "[blue]Database Answer:[/blue]",
        #         f"[green]{title}[/green] -",
        #         url,
        #         # "\n",
        #         # answer,
        #     )
        #     print("[blue]GPT Response:[/blue]", gpt_response)

    except KeyboardInterrupt:
        logger.warning("Exiting program, have a nice day :)")
