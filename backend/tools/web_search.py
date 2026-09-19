import logging
from ddgs import DDGS
from backend.models.schemas import SearchResult

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 10) -> list[SearchResult]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of SearchResult objects with title, url, and snippet.
    """
    results = []
    try:
        ddgs = DDGS()
        search_results = ddgs.text(
            query,
            max_results=max_results,
        )
        for r in search_results:
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", r.get("link", "")),
                    snippet=r.get("body", r.get("snippet", "")),
                )
            )
        logger.info(f"Web search for '{query}': {len(results)} results")
    except Exception as e:
        logger.error(f"Web search failed for '{query}': {e}")
    return results
