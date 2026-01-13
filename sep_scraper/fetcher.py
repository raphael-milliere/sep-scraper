"""HTTP fetching utilities for SEP scraper."""

import re
from urllib.parse import urlparse, urljoin

import httpx


class ScraperError(Exception):
    """Raised when scraping fails."""

    pass


async def fetch_mathjax_macros(article_url: str) -> dict[str, tuple[str, int]]:
    """Fetch custom MathJax macros from article's local.js file.

    Args:
        article_url: SEP article URL

    Returns:
        Dictionary mapping macro names to (expansion, num_args) tuples
    """
    # Construct local.js URL
    if not article_url.endswith("/"):
        article_url += "/"
    local_js_url = urljoin(article_url, "local.js")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(local_js_url, follow_redirects=True)
            if response.status_code != 200:
                return {}
            return _parse_mathjax_macros(response.text)
        except httpx.RequestError:
            return {}


def _parse_mathjax_macros(js_content: str) -> dict[str, tuple[str, int]]:
    """Parse MathJax macro definitions from local.js content.

    Args:
        js_content: JavaScript content from local.js

    Returns:
        Dictionary mapping macro names to (expansion, num_args) tuples
    """
    macros = {}

    # Find the Macros section - use balanced brace matching
    macros_start = js_content.find("Macros")
    if macros_start == -1:
        return macros

    # Find the opening brace after Macros
    brace_start = js_content.find("{", macros_start)
    if brace_start == -1:
        return macros

    # Find matching closing brace (handle nested braces)
    depth = 1
    pos = brace_start + 1
    while pos < len(js_content) and depth > 0:
        if js_content[pos] == "{":
            depth += 1
        elif js_content[pos] == "}":
            depth -= 1
        pos += 1

    macros_section = js_content[brace_start + 1 : pos - 1]

    # Pattern for simple string format: macroName: "expansion" or 'expansion'
    simple_pattern = re.compile(
        r'(\w+)\s*:\s*(?:"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')\s*(?:,|$)',
        re.MULTILINE,
    )

    # Pattern for array format: macroName: ["expansion"] or ["expansion", numArgs]
    array_pattern = re.compile(
        r'(\w+)\s*:\s*\[\s*"((?:[^"\\]|\\.)*)"\s*(?:,\s*(\d+))?\s*\]',
        re.MULTILINE,
    )

    def decode_js_escapes(value: str) -> str:
        """Decode JavaScript escape sequences."""
        value = value.replace("\\\\", "\x00")  # Temp placeholder
        value = value.replace("\\", "")  # Remove single escapes
        value = value.replace("\x00", "\\")  # Restore double as single
        return value

    # Parse simple format (no arguments)
    for match in simple_pattern.finditer(macros_section):
        name = match.group(1)
        value = match.group(2) or match.group(3)
        if value:
            macros[name] = (decode_js_escapes(value), 0)

    # Parse array format (may have arguments)
    for match in array_pattern.finditer(macros_section):
        name = match.group(1)
        value = match.group(2)
        num_args = int(match.group(3)) if match.group(3) else 0
        if value:
            macros[name] = (decode_js_escapes(value), num_args)

    return macros


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
