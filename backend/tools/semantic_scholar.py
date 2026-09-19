"""Semantic Scholar API search — aggregates IEEE, ACM, PubMed, Arxiv, Springer, etc."""
import logging
import httpx
from backend.models.schemas import PaperResult

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_semantic_scholar(query: str, max_results: int = 5) -> list[PaperResult]:
    """
    Search Semantic Scholar for academic papers from multiple publishers.

    Covers: IEEE, ACM, PubMed, Arxiv, Springer, Elsevier, AAAI, NeurIPS, etc.
    Free API, no key required. Rate limit: 100 requests/5 min.
    """
    try:
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract,url,externalIds,venue,citationCount",
        }

        response = httpx.get(SEMANTIC_SCHOLAR_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        papers = []
        for paper in data.get("data", []):
            # Build URL — prefer DOI, then Semantic Scholar page
            external_ids = paper.get("externalIds") or {}
            doi = external_ids.get("DOI")
            arxiv_id = external_ids.get("ArXiv")

            if doi:
                url = f"https://doi.org/{doi}"
            elif arxiv_id:
                url = f"https://arxiv.org/abs/{arxiv_id}"
            else:
                paper_id = paper.get("paperId", "")
                url = f"https://www.semanticscholar.org/paper/{paper_id}"

            # Determine source/venue
            venue = paper.get("venue") or ""
            source_tag = _identify_source(venue, external_ids)

            # Authors
            authors = ", ".join(
                a.get("name", "") for a in (paper.get("authors") or [])[:3]
            )
            if len(paper.get("authors") or []) > 3:
                authors += " et al."

            title = paper.get("title") or "Untitled"
            year = paper.get("year") or ""
            citations = paper.get("citationCount") or 0

            papers.append(
                PaperResult(
                    title=f"[{source_tag}] {title}" if source_tag else title,
                    authors=authors,
                    url=url,
                    abstract=paper.get("abstract") or "",
                    year=str(year),
                )
            )

        logger.info(
            f"Semantic Scholar search for '{query}': {len(papers)} papers found"
        )
        return papers

    except Exception as e:
        logger.error(f"Semantic Scholar search failed for '{query}': {e}")
        return []


def _identify_source(venue: str, external_ids: dict) -> str:
    """Identify the paper source from venue name or external IDs."""
    venue_lower = venue.lower() if venue else ""

    if external_ids.get("ArXiv"):
        return "ArXiv"
    if "ieee" in venue_lower or external_ids.get("IEEE"):
        return "IEEE"
    if "acm" in venue_lower or external_ids.get("ACL"):
        return "ACM"
    if external_ids.get("PubMed") or external_ids.get("PMID"):
        return "PubMed"
    if "neurips" in venue_lower or "nips" in venue_lower:
        return "NeurIPS"
    if "icml" in venue_lower:
        return "ICML"
    if "aaai" in venue_lower:
        return "AAAI"
    if "springer" in venue_lower:
        return "Springer"
    if "elsevier" in venue_lower or "sciencedirect" in venue_lower:
        return "Elsevier"
    if "cvpr" in venue_lower or "iccv" in venue_lower or "eccv" in venue_lower:
        return "CV Conf"
    if venue:
        return venue[:20]  # Use venue name if known
    return ""
