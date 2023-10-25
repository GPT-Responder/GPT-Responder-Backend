import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

    chatgpt = ChatGPT()

    prompt = f"Question: {question}\nContext: {context} URL: {url}"
    token_count = chatgpt.string_to_tokens(prompt)
    
    if token_count > 4096:
        logger.warning(f"Prompt is too long ({token_count} tokens), using 16k model instead")
        gpt_response = chatgpt.prompt(prompt, role, model="gpt-3.5-turbo-16k")
    else:
        gpt_response = chatgpt.prompt(prompt, role)

    gpt_response = gpt_response["choices"][0]["message"]["content"]
    
    return { "response": gpt_response }

if __name__ == "__main__":
    config = uvicorn.Config("api:app", port=5000, log_level="info", log_config=None, use_colors=False)
    server = uvicorn.Server(config)
    server.run()
