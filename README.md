# Agentic Research Platform

A **Multi-Agent AI Research & Fact-Checking Platform** that uses multiple specialized AI agents to conduct academic research, extract findings, cross-reference facts, and generate structured research reports with citations.

## Architecture

```
User Question (POST /research)
       ↓
┌──────────────┐
│ Router Agent │  ← Analyzes query, creates research plan
└──────┬───────┘
       ↓
┌──────────────────┐
│ Research Agent    │  ← Searches web (DuckDuckGo) + Arxiv
│  ├── Web Search  │     Scrapes content from top results
│  └── Paper Search│     Pulls paper abstracts
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Extraction Agent │  ← Extracts key findings, methodologies,
│                  │     evidence from each source
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Fact-Check Agent │  ← Cross-references claims across sources,
│                  │     identifies agreements/contradictions
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Synthesis Agent  │  ← Generates structured research report
│                  │     with citations and confidence scores
└──────────────────┘
       ↓
   Research Report (JSON with markdown report + sources)
```

## Features

- **Multi-Agent Pipeline**: 5 specialized agents working in sequence
- **Web Search**: DuckDuckGo integration (free, no API key needed)
- **Academic Search**: Arxiv paper search with abstracts
- **Content Extraction**: Web scraping for full article content
- **Fact-Checking**: Cross-references claims across multiple sources
- **LLM Abstraction**: Supports Groq (free API) and Ollama (local) with automatic fallback
- **Structured Output**: JSON research reports with citations, confidence scores, and agent execution traces

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure LLM provider

Copy `.env.example` to `.env` and add your Groq API key:
```bash
cp .env.example .env
# Edit .env with your GROQ_API_KEY (free at https://console.groq.com)
```

Or use Ollama locally (no API key needed):
```bash
# Set LLM_PROVIDER=ollama in .env
ollama pull gemma2:9b
```

### 3. Run the server
```bash
uvicorn backend.main:app --reload
```

### 4. Test it
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Find recent research on using LLMs for cybersecurity threat detection"}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/ask` | GET | Simple Q&A (direct LLM call) |
| `/research` | POST | Full multi-agent research pipeline |
| `/health` | GET | Platform & provider status |
| `/docs` | GET | Interactive API documentation (Swagger) |

## Project Structure

```
backend/
├── main.py              # FastAPI app with endpoints
├── config.py            # Configuration & env vars
├── pipeline.py          # Agent orchestration
├── llm/                 # LLM provider abstraction
│   ├── base.py          # Abstract interface
│   ├── groq_provider.py # Groq (free API)
│   ├── ollama_provider.py # Ollama (local)
│   └── factory.py       # Provider factory with fallback
├── tools/               # Search & scraping tools
│   ├── web_search.py    # DuckDuckGo search
│   ├── arxiv_search.py  # Academic paper search
│   └── web_scraper.py   # URL content extraction
├── models/              # Pydantic data models
│   └── schemas.py       # All request/response schemas
└── agents/              # Specialized AI agents
    ├── base.py          # Base agent class
    ├── router_agent.py  # Query → research plan
    ├── research_agent.py # Plan → search results
    ├── extraction_agent.py # Results → structured findings
    ├── factcheck_agent.py  # Findings → fact-check results
    └── synthesis_agent.py  # Everything → research report
```

## Tech Stack

- **FastAPI** — API server
- **Groq / Ollama** — LLM providers
- **DuckDuckGo** — Web search (free)
- **Arxiv** — Academic paper search
- **Pydantic** — Data validation
- **BeautifulSoup** — Web scraping