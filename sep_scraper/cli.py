"""Command-line interface for SEP scraper."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from sep_scraper.fetcher import (
    fetch_article,
    fetch_mathjax_macros,
    fetch_appendices,
    validate_sep_url,
    ScraperError,
)
from sep_scraper.parser import SEPParser
from sep_scraper.assembler import assemble_markdown


logger = logging.getLogger("sep_scraper")


def extract_entry_name(url: str) -> str:
    """Extract entry name from SEP URL.

    Args:
        url: SEP article URL

    Returns:
        Entry name (e.g., "consciousness")
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return path.split("/")[-1]


async def scrape_article(url: str) -> str:
    """Scrape a SEP article and convert to markdown.

    Args:
        url: SEP article URL

    Returns:
        Markdown string

    Raises:
        ScraperError: If scraping fails
        ValueError: If URL is invalid
    """
    # Validate URL
    validate_sep_url(url)

    # Fetch HTML and macros concurrently
    html, macros = await asyncio.gather(
        fetch_article(url),
        fetch_mathjax_macros(url),
    )

    # Parse main article
    soup = BeautifulSoup(html, "lxml")
    parser = SEPParser(soup, url, macros)

    # Extract appendix links and fetch appendices
    appendix_links = parser.get_appendix_links()
    appendix_pages = await fetch_appendices(appendix_links)

    # Parse each appendix
    appendices = []
    for title, appendix_html in appendix_pages:
        appendix_soup = BeautifulSoup(appendix_html, "lxml")
        appendix_content = parser.parse_appendix(appendix_soup)
        if appendix_content:
            appendices.append((title, appendix_content))

    # Extract other components
    metadata = parser.get_metadata()
    content = parser.get_main_content()
    footnotes = parser.get_footnotes()
    bibliography = parser.get_bibliography()

    # Assemble with appendices
    return assemble_markdown(metadata, content, footnotes, bibliography, appendices)


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Convert Stanford Encyclopedia of Philosophy articles to markdown",
        prog="sep-scraper",
    )
    parser.add_argument(
        "url",
        help="Full URL to SEP article (e.g., https://plato.stanford.edu/entries/consciousness/)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path",
        type=Path,
    )
    parser.add_argument(
        "-d", "--directory",
        help="Output directory (auto-names file from entry)",
        type=Path,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Validate URL early
    try:
        validate_sep_url(args.url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Run scraper
    try:
        markdown = asyncio.run(scrape_article(args.url))
    except ScraperError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    elif args.directory:
        args.directory.mkdir(parents=True, exist_ok=True)
        entry_name = extract_entry_name(args.url)
        output_path = args.directory / f"{entry_name}.md"
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
