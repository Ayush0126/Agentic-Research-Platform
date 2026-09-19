from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Input ---

class ResearchRequest(BaseModel):
    """User's research query input."""
    query: str = Field(..., description="The research question to investigate")


# --- Search Tool Outputs ---

class SearchResult(BaseModel):
    """A single web search result."""
    title: str
    url: str
    snippet: str


class PaperResult(BaseModel):
    """An academic paper search result from Arxiv."""
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: Optional[str] = None


# --- Pipeline Intermediate Models ---

class ResearchPlan(BaseModel):
    """Output of the Router Agent: a plan for conducting research."""
    original_query: str
    search_queries: list[str] = Field(
        description="Targeted search queries to run (3-5 queries)"
    )
    key_aspects: list[str] = Field(
        description="Key aspects/dimensions to investigate"
    )


class SourceContent(BaseModel):
    """Content scraped/extracted from a source URL."""
    url: str
    title: str
    content: str
    source_type: str = "web"  # 'web' or 'arxiv'


class ExtractedFinding(BaseModel):
    """A structured finding extracted from a source."""
    claim: str = Field(description="The key claim or finding")
    evidence: str = Field(description="Supporting evidence from the source")
    methodology: Optional[str] = Field(
        None, description="Research methodology used, if applicable"
    )
    source_url: str
    source_title: str


class FactCheckResult(BaseModel):
    """Result of cross-referencing a claim across multiple sources."""
    claim: str
    supporting_sources: list[str] = Field(
        description="URLs of sources that support this claim"
    )
    contradicting_sources: list[str] = Field(
        description="URLs of sources that contradict this claim"
    )
    nuance: str = Field(
        description="Additional context, caveats, or nuance"
    )
    confidence: float = Field(
        description="Confidence score 0.0-1.0",
        ge=0.0,
        le=1.0
    )


# --- Final Output ---

class ResearchReport(BaseModel):
    """The final structured research report."""
    title: str
    query: str
    summary: str = Field(description="Executive summary of findings")
    key_findings: list[dict] = Field(
        description="List of key findings, each with 'finding' and 'details' keys"
    )
    methodology_overview: str = Field(
        description="Overview of methodologies found across sources"
    )
    fact_check_results: list[FactCheckResult] = Field(
        description="Fact-check results for key claims"
    )
    research_gaps: list[str] = Field(
        description="Identified gaps in the current research"
    )
    sources: list[dict] = Field(
        description="All sources used, each with 'title' and 'url' keys"
    )
    agent_trace: list[dict] = Field(
        default_factory=list,
        description="Execution trace: agent name, duration, status"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
