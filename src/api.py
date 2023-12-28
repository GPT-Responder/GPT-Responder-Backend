import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from weaviate_handler import WeaviateHandler
from chat_gpt import ChatGPT
from logger_setup import setup_logger

logger = setup_logger()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.get("/question/{question}")
async def question(question):
    weaviate = WeaviateHandler()

    response = weaviate.vector_search(
        "Webpage",
        question,
        ["title", "content", "url"],
        hybrid_properties=["mostCommonQuestions^3", "content", 'title^5'],
    )

    role = "You are an admissions officer at Stetson univerisity. Using only the context provided, you will answer emailed questions. Do not add an email signature. Make sure to always include the webpage link."
    context = response["data"]["Get"]["Webpage"][0]["content"]
    url = response["data"]["Get"]["Webpage"][0]["url"]

    chatgpt = ChatGPT()

    prompt_content = f"Question: {question}\nContext: {context} URL: {url}"
    token_count = chatgpt.string_to_tokens(prompt_content)

    def chat_stream():
        model_name = "gpt-3.5-turbo-16k" if token_count > 4000 else "gpt-4"
        logger.info(f"Using model: {model_name}")
        
        for message in chatgpt.prompt(prompt_content, role, model=model_name):
            if message['choices'][0]['finish_reason'] is not None:
                break
            yield message['choices'][0]['delta']['content']  # adding a new line as a message delimiter

    return StreamingResponse(chat_stream(), media_type="text/plain")

if __name__ == "__main__":
    config = uvicorn.Config("api:app", host="0.0.0.0", port=5000, log_level="info", log_config=None, use_colors=False)
    server = uvicorn.Server(config)
    server.run()
