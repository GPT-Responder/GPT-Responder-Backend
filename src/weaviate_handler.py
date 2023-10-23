import weaviate
import logging
import os

from dotenv import load_dotenv
from logger_setup import setup_logger

logger = setup_logger()
load_dotenv()


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

        auth_config = weaviate.AuthApiKey(api_key=weaviate_api_key)
        # self.client = weaviate.Client(url=weaviate_url, auth_client_secret=auth_config)
        self.client = weaviate.Client(url=weaviate_url)

        logger.info("Connected to Weaviate database")

    # TODO: rewrite this to create new classes
    def add_schema(self, schema):
        # TODO: figure out how to check if the class is already made

        self.client.schema.create_class(schema)

    def batch_add(self, data, batch_size=100):
        with self.client.batch as batch:
            batch.batch_size = batch_size

            for i, d in enumerate(data):
                logger.debug(f"Adding the following to Weaviate database:\n{d}")
                properties = {
                    "title": d["title"],
                    "url": d["url"],
                    "content": d["content"],
                    "mostCommonQuestions": d["mostCommonQuestions"],
                }
                self.client.batch.add_data_object(properties, "Webpage")
        logger.debug("Content added to Weaviate database")

    def vector_search(
        self,
        class_name,
        concepts,
        properties,
        limit=1,
        hybrid_properties=None,
        move_to=None,
        move_away_from=None,
        force=0.5,
    ):
        """
        Perform a vector search on a Weaviate class.

        Parameters:
        - class_name: The name of the class to search.
        - concepts: A string to search for.
        - properties: A list of properties to return in the search results.
        - limit: The maximum number of results to return.
        - move_to: An optional list of concepts to move towards in the search.
        - move_away_from: An optional list of concepts to move away from in the
          search.
        - force: The force to apply when moving towards or away from concepts
          (default is 0.5).
        """

        logger.info(
            f'Performing vector search on class {class_name} for concepts "{concepts}"'
        )

        # Define the search parameters
        search_params = {
            "concepts": concepts,
        }

        # Optionally move towards certain concepts
        if move_to is not None:
            search_params["moveTo"] = {"values": move_to, "force": force}

        # Optionally move away from certain concepts
        if move_away_from is not None:
            search_params["moveAwayFrom"] = {"values": move_away_from, "force": force}

        # Perform the search
        # TODO: Figure out why hybrid search is not working 
        try:
            if hybrid_properties is None:
                query = self.client.query.get(class_name, properties)
                result = query.with_near_text(search_params).with_limit(limit).do()
            else:
                query = self.client.query.get(class_name, properties).with_hybrid(query=concepts, properties=hybrid_properties)
                result = query.with_near_text(search_params).with_limit(limit).do()
            logger.info(f"Vector search completed successfully.")
        except Exception as e:
            logger.error(f"Vector search failed with error: {e}")
            return None

        return result

    def get_batch_with_cursor(
        self, class_name, class_properties, batch_size, cursor=None
    ):
        query = (
            self.client.query.get(class_name, class_properties)
            # Optionally retrieve the vector embedding by adding `vector` to the _additional fields
            .with_additional(["id vector"]).with_limit(batch_size)
        )

        if cursor is not None:
            return query.with_after(cursor).do()
        else:
            return query.do()

