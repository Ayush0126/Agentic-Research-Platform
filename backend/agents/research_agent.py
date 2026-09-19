import logging
from backend.agents.base import BaseAgent
from backend.llm.base import LLMProvider
from backend.models.schemas import ResearchPlan, SearchResult, PaperResult, SourceContent
from backend.tools.web_search import search_web
from backend.tools.arxiv_search import search_papers
from backend.tools.web_scraper import scrape_url
from backend.config import settings

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent: Takes the research plan from the Router Agent,
    executes web + arxiv searches, and scrapes content from top results.
    """

    def __init__(self, llm: LLMProvider):
        super().__init__(
            llm=llm,
            name="Research Agent",
            role="Information Gatherer",
            system_prompt="You are a research assistant that gathers information.",
        )

    def run(self, plan: ResearchPlan) -> dict:
        """
        Execute searches based on the research plan and scrape content.

        Args:
            plan: The ResearchPlan from the Router Agent.

        Returns:
            dict with 'web_results', 'paper_results', 'scraped_content' keys.
        """
        all_web_results: list[SearchResult] = []
        all_paper_results: list[PaperResult] = []
        scraped_content: list[SourceContent] = []
        seen_urls: set[str] = set()

        for query in plan.search_queries:
            # Web search
            logger.info(f"[Research] Web searching: {query}")
            web_results = search_web(query, max_results=settings.max_search_results)
            for result in web_results:
                if result.url not in seen_urls:
                    all_web_results.append(result)
                    seen_urls.add(result.url)

            # Arxiv search
            logger.info(f"[Research] Arxiv searching: {query}")
            paper_results = search_papers(query, max_results=settings.max_arxiv_results)
            for paper in paper_results:
                if paper.url not in seen_urls:
                    all_paper_results.append(paper)
                    seen_urls.add(paper.url)

        # Scrape content from top web results (limit to avoid too many requests)
        max_scrape = min(2, len(all_web_results))
        logger.info(f"[Research] Scraping top {max_scrape} web results...")
        for result in all_web_results[:max_scrape]:
            content = scrape_url(result.url, timeout=settings.scrape_timeout)
            if not content.startswith("[Failed"):
                scraped_content.append(
                    SourceContent(
                        url=result.url,
                        title=result.title,
                        content=content,
                        source_type="web",
                    )
                )

        # Add arxiv paper abstracts as content (limit for performance)
        for paper in all_paper_results[:2]:
            scraped_content.append(
                SourceContent(
                    url=paper.url,
                    title=paper.title,
                    content=f"Title: {paper.title}\n"
                            f"Authors: {', '.join(paper.authors)}\n"
                            f"Published: {paper.published or 'N/A'}\n"
                            f"Abstract: {paper.abstract}",
                    source_type="arxiv",
                )
            )

        logger.info(
            f"[Research] Collected {len(all_web_results)} web results, "
            f"{len(all_paper_results)} papers, "
            f"{len(scraped_content)} sources with content"
        )

        return {
            "web_results": all_web_results,
            "paper_results": all_paper_results,
            "scraped_content": scraped_content,
        }
