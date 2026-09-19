import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from ollama import chat
from backend.models.schemas import ResearchRequest, ResearchReport
from backend.pipeline import ResearchPipeline
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Research Platform",
    description="Multi-Agent AI Research & Fact-Checking Platform",
    version="1.0.0",
)

# CORS middleware for future frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/research", response_model=ResearchReport)
def run_research(request: ResearchRequest):
    """
    Run the full multi-agent research pipeline.

    Takes a research question and returns a structured report with:
    - Executive summary
    - Key findings with evidence
    - Fact-check results with confidence scores
    - Research gaps
    - Full source citations
    - Agent execution trace
    """
    logger.info(f"Received research request: {request.query}")

    try:
        pipeline = ResearchPipeline()
        report = pipeline.run(request.query)
        return report
    except Exception as e:
        logger.error(f"Research pipeline failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Research pipeline failed: {str(e)}"
        )


@app.get("/health")
def health_check():
    """Check the health of the platform and available providers."""
    status = {
        "platform": "running",
        "llm_provider": settings.llm_provider,
        "groq_configured": bool(settings.groq_api_key),
        "groq_model": settings.groq_model,
        "ollama_model": settings.ollama_model,
    }

    # Check Groq availability
    if settings.groq_api_key:
        try:
            from backend.llm.groq_provider import GroqProvider
            provider = GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
            status["groq_available"] = provider.is_available()
        except Exception:
            status["groq_available"] = False
    else:
        status["groq_available"] = False

    # Check Ollama availability
    try:
        from backend.llm.ollama_provider import OllamaProvider
        provider = OllamaProvider(model=settings.ollama_model)
        status["ollama_available"] = provider.is_available()
    except Exception:
        status["ollama_available"] = False

    return status


# ── Frontend serving ──────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/app")
def serve_frontend():
    """Serve the frontend application."""
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount static files (CSS, JS) — must be after route definitions
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")