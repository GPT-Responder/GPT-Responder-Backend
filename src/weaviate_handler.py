import weaviate
import logging
import os

from logger import setup_logger

logger = setup_logger(__name__)

class WeaviateHandler:
    def __init__(self):
        logger.info("Setting up Weaviate Client")

        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        weaviate_url = os.getenv("WEAVIATE_URL")

        logger.info("Checking if API Keys exist")

        # TODO: Check if there is a better way to write this
        if weaviate_api_key is None:
            error_message = "WEAVIATE_API_KEY environment variable is not set."
            logger.error(error_message)
            raise ValueError(error_message)

        if weaviate_url is None:
            error_message = "WEAVIATE_URL environment variable is not set."
            logger.error(error_message)
            raise ValueError(error_message)

        logger.info("API Keys exist, connecting to database")

        # auth_config = weaviate.AuthApiKey(api_key=weaviate_api_key)

        # self.client = weaviate.Client(
        #     url=weaviate_url,
        #     auth_client_secret=auth_config
        # )
        
        self.client = weaviate.Client(weaviate_url)

        logger.info("Connected to Weaviate database")

    # TODO: rewrite this to create new classes
    def setup_weaviate_db(self):
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
            ],
        }

        # weaviate.schema.create_class(website)

    def batch_add(data, batch_size=100):
        with weaviate.batch as batch:
            batch.batch_size = batch_size

            for i, d in enumerate(data):
                logger.debug(f"Adding the following to Weaviate database:\n{d}")
                properties = {
                    "title": d["title"],
                    "url": d["url"],
                    "content": d["content"],
                }
                weaviate.batch.add_data_object(properties, "Webpage")
        logger.debug(f"Content added to Weaviate database")

        return True  # TODO: make this return false if getting the webpage fails
