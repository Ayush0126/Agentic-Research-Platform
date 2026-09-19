import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def scrape_url(url: str, timeout: int = 10) -> str:
    """
    Fetch and extract clean text content from a URL.

    Args:
        url: The URL to scrape.
        timeout: Request timeout in seconds.

    Returns:
        Extracted text content (truncated to ~3000 chars for LLM context).
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Extract text
        text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Truncate to ~3000 chars to keep LLM context manageable
        max_chars = 3000
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "\n... [content truncated]"

        logger.info(f"Scraped {url}: {len(clean_text)} chars")
        return clean_text

    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return f"[Failed to retrieve content from {url}]"
