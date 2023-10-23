import uvicorn
from fastapi import FastAPI
from weaviate_handler import WeaviateHandler
from chat_gpt import ChatGPT
from logger_setup import setup_logger

logger = setup_logger()
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.get("/question/{question}")
async def question(question: str):
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
    title = response["data"]["Get"]["Webpage"][0]["title"]

    chatgpt = ChatGPT()

    content = f"Question: {question}\nContext: {context} URL: {url}"
    gpt_response = chatgpt.prompt(content, role=role)["choices"][0]["message"]["content"]
    
    return { "response": gpt_response }

if __name__ == "__main__":
    config = uvicorn.Config("api:app", port=5000, log_level="info", log_config=None, use_colors=False)
    server = uvicorn.Server(config)
    server.run()
