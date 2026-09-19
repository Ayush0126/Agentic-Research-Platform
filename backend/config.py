import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # LLM Provider
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma2:9b")

    # Search settings
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "3"))
    max_arxiv_results: int = int(os.getenv("MAX_ARXIV_RESULTS", "2"))

    # Scraper settings
    scrape_timeout: int = int(os.getenv("SCRAPE_TIMEOUT", "10"))

    # LLM settings
    llm_temperature: float = 0.3
    llm_max_tokens: int = 900  # Groq free tier limit: 1000 output tokens/min

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
