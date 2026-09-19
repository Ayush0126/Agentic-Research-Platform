import logging
import arxiv
from backend.models.schemas import PaperResult

logger = logging.getLogger(__name__)


def search_papers(query: str, max_results: int = 5) -> list[PaperResult]:
    """
    Search for academic papers on Arxiv.

    Args:
        query: The search query for academic papers.
        max_results: Maximum number of papers to return.

    Returns:
        List of PaperResult objects with title, authors, abstract, url, published.
    """
    results = []
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        for paper in client.results(search):
            results.append(
                PaperResult(
                    title=paper.title,
                    authors=[a.name for a in paper.authors],
                    abstract=paper.summary,
                    url=paper.entry_id,
                    published=paper.published.strftime("%Y-%m-%d") if paper.published else None,
                )
            )
        logger.info(f"Arxiv search for '{query}': {len(results)} papers found")
    except Exception as e:
        logger.error(f"Arxiv search failed for '{query}': {e}")
    return results
