"""Metadata extraction from SEP articles."""

import re
from datetime import datetime

from bs4 import BeautifulSoup


MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_date(date_str: str) -> str | None:
    """Parse SEP date format to ISO format.

    Args:
        date_str: Date string like "Tue Jun 18, 2004"

    Returns:
        ISO format date string or None if parsing fails
    """
    # Pattern: Day Mon DD, YYYY
    pattern = r"([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})"
    match = re.search(pattern, date_str)
    if not match:
        return None

    month_str, day, year = match.groups()
    month = MONTH_MAP.get(month_str.lower())
    if not month:
        return None

    try:
        date = datetime(int(year), month, int(day))
        return date.strftime("%Y-%m-%d")
    except ValueError:
        return None


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """Extract article metadata from parsed HTML.

    Args:
        soup: Parsed HTML document
        url: Source URL of the article

    Returns:
        Dictionary with title, author, published, revised, url
    """
    metadata = {"url": url}

    # Extract title from h1
    if h1 := soup.find("h1"):
        metadata["title"] = h1.get_text(strip=True)
    else:
        metadata["title"] = None

    # Extract dates from preamble
    # Look for text like "First published ... ; substantive revision ..."
    date_pattern = re.compile(r"first published|substantive revision", re.I)
    for elem in soup.find_all(["p", "em"]):
        text = elem.get_text()
        if date_pattern.search(text):
            # Extract first published date
            if pub_match := re.search(r"first published\s+(.+?)(?:;|$)", text, re.I):
                metadata["published"] = _parse_date(pub_match.group(1))

            # Extract revision date
            if rev_match := re.search(r"substantive revision\s+(.+?)(?:;|$)", text, re.I):
                metadata["revised"] = _parse_date(rev_match.group(1))
            break

    # Set defaults for missing dates
    metadata.setdefault("published", None)
    metadata.setdefault("revised", None)

    # Extract author from copyright section
    metadata["author"] = None
    if copyright_div := soup.find("div", id="article-copyright"):
        # Author name is typically in an anchor tag or before email
        if author_link := copyright_div.find("a"):
            metadata["author"] = author_link.get_text(strip=True)
        else:
            # Try to extract from text before email
            text = copyright_div.get_text()
            if author_match := re.search(r"by\s*\n?\s*(.+?)(?:\s*<|$)", text):
                metadata["author"] = author_match.group(1).strip()

    return metadata


def _quote_value(value) -> str:
    """Format a value for YAML frontmatter with appropriate quoting.

    Args:
        value: The value to format

    Returns:
        Formatted string value
    """
    if value is None:
        return "null"
    # Quote strings
    if isinstance(value, str):
        # Escape any double quotes in the string
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def format_frontmatter(metadata: dict) -> str:
    """Format metadata as YAML frontmatter.

    Args:
        metadata: Dictionary of metadata fields

    Returns:
        YAML frontmatter string with --- delimiters
    """
    # Order fields consistently
    fields = [
        ("title", metadata.get("title")),
        ("author", metadata.get("author")),
        ("published", metadata.get("published")),
        ("revised", metadata.get("revised")),
        ("url", metadata.get("url")),
    ]

    lines = ["---"]
    for key, value in fields:
        lines.append(f"{key}: {_quote_value(value)}")
    lines.append("---")

    return "\n".join(lines) + "\n"
