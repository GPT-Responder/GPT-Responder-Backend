import openai
import os
import tiktoken
from logger_setup import setup_logger

logger = setup_logger(logger_name=__name__)

class ChatGPT:
    def __init__(self):
        logger.info("Authenicating with OpenAI")
        openai.api_key = os.getenv(
            "OPENAI_API_KEY"
        )

    def prompt(self, content, role = "You are a helpful assistant.", model="gpt-3.5-turbo"):
        logger.info(f"Asking {model}")
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": content},
            ],
        )

        return response

    def string_to_tokens(self, string, encoding="gpt-3.5-turbo"):
        encoding = tiktoken.encoding_for_model(encoding)
        num_tokens = len(encoding.encode(string))
        return num_tokens

