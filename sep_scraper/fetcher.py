"""HTTP fetching utilities for SEP scraper."""

from urllib.parse import urlparse

import httpx


class ScraperError(Exception):
    """Raised when scraping fails."""

    pass


def validate_sep_url(url: str) -> str:
    """Validate that URL is a SEP article URL.

    Args:
        url: URL to validate

    Returns:
        The validated URL

    Raises:
        ValueError: If URL is not a valid SEP article URL
    """
    parsed = urlparse(url)
    valid_domains = ("plato.stanford.edu", "seop.illc.uva.nl")

    if parsed.netloc not in valid_domains:
        raise ValueError(f"Not a SEP URL: {url}")

    if not parsed.path.startswith("/entries/"):
        raise ValueError(f"Not an article URL: {url}")

    return url


async def fetch_article(url: str) -> str:
    """Fetch HTML content from a SEP article URL.

    Args:
        url: SEP article URL

    Returns:
        HTML content as string

    Raises:
        ScraperError: If fetching fails
    """
    validate_sep_url(url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException:
            raise ScraperError(f"Timeout fetching {url}")
        except httpx.HTTPStatusError as e:
            raise ScraperError(f"HTTP {e.response.status_code} for {url}")
        except httpx.RequestError as e:
            raise ScraperError(f"Network error: {e}")
