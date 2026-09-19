from dotenv import load_dotenv
import os

load_dotenv()

print("GROQ KEY LOADED:", bool(os.getenv("GROQ_API_KEY")))
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI()

# Allow your frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get Groq API key from .env
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


@app.get("/")
def home():
    return {
        "message": "Agentic Research Platform is running!"
    }


@app.get("/ask")
def ask_question(question: str):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return {
        "question": question,
        "answer": response.choices[0].message.content
    }


@app.post("/research")
def research(data: dict):

    question = data.get("question", "")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return {
        "question": question,
        "answer": response.choices[0].message.content
    }