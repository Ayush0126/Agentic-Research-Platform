from fastapi import FastAPI
from ollama import chat

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Agentic Research Platform is running!"}


@app.get("/ask")
def ask_question(question: str):
    response = chat(
        model="qwen2.5:7b",
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return {
        "question": question,
        "answer": response.message.content
    }