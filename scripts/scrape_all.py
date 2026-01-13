#!/usr/bin/env python3
"""Scrape all SEP entries to markdown files."""

import asyncio
import sys
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

# Add parent directory to path for sep_scraper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sep_scraper.cli import scrape_article
from sep_scraper.fetcher import ScraperError


BASE_URL = "https://plato.stanford.edu"
CONTENTS_URL = "https://plato.stanford.edu/contents.html"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
CONCURRENCY = 20  # Number of concurrent requests


async def get_all_entry_urls() -> list[str]:
    """Fetch the table of contents and extract all entry URLs."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(CONTENTS_URL)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    urls = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "entries/" in href:
            # Normalize URL
            if href.startswith("/"):
                url = urljoin(BASE_URL, href)
            elif href.startswith("http"):
                url = href
            else:
                url = urljoin(BASE_URL + "/", href)

            # Ensure trailing slash
            if not url.endswith("/"):
                url += "/"

            urls.add(url)

    return sorted(urls)


async def scrape_entry(url: str, output_dir: Path, semaphore: asyncio.Semaphore) -> tuple[str, bool, str]:
    """Scrape a single entry and save to file.

    Returns: (url, success, message)
    """
    entry_name = url.rstrip("/").split("/")[-1]
    output_path = output_dir / f"{entry_name}.md"

    # Skip if already scraped
    if output_path.exists():
        return (url, True, "exists")

    async with semaphore:
        try:
            markdown = await scrape_article(url)
            output_path.write_text(markdown, encoding="utf-8")
            return (url, True, "done")
        except ScraperError as e:
            return (url, False, str(e))
        except Exception as e:
            return (url, False, f"error: {e}")


async def main():
    """Main entry point."""
    print("Fetching list of all SEP entries...")
    urls = await get_all_entry_urls()
    print(f"Found {len(urls)} entries to scrape.\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check how many already exist
    existing = sum(1 for url in urls if (OUTPUT_DIR / f"{url.rstrip('/').split('/')[-1]}.md").exists())
    print(f"Already scraped: {existing}, remaining: {len(urls) - existing}\n")

    # Semaphore for concurrency control
    semaphore = asyncio.Semaphore(CONCURRENCY)

    # Create all tasks
    tasks = [scrape_entry(url, OUTPUT_DIR, semaphore) for url in urls]

    # Track progress
    success_count = 0
    skip_count = 0
    fail_count = 0
    failed_urls = []

    # Process with progress reporting
    for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        url, success, message = await coro
        entry_name = url.rstrip("/").split("/")[-1]

        if success:
            if message == "exists":
                skip_count += 1
            else:
                success_count += 1
                print(f"[{i}/{len(urls)}] {entry_name}: {message}")
        else:
            fail_count += 1
            failed_urls.append((url, message))
            print(f"[{i}/{len(urls)}] {entry_name}: FAILED - {message}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Completed: {success_count} scraped, {skip_count} skipped, {fail_count} failed")
    print(f"Output directory: {OUTPUT_DIR}")

    if failed_urls:
        print(f"\nFailed entries ({len(failed_urls)}):")
        for url, error in failed_urls[:20]:  # Show first 20
            entry = url.rstrip("/").split("/")[-1]
            print(f"  - {entry}: {error}")
        if len(failed_urls) > 20:
            print(f"  ... and {len(failed_urls) - 20} more")


if __name__ == "__main__":
    asyncio.run(main())
