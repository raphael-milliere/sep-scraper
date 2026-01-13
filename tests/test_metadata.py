"""Tests for metadata extraction."""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from sep_scraper.metadata import extract_metadata, format_frontmatter


@pytest.fixture
def sample_soup():
    html_path = Path(__file__).parent / "fixtures" / "sample_preamble.html"
    html = html_path.read_text()
    return BeautifulSoup(html, "lxml")


class TestExtractMetadata:
    def test_extracts_title(self, sample_soup):
        metadata = extract_metadata(sample_soup, "https://plato.stanford.edu/entries/consciousness/")
        assert metadata["title"] == "Consciousness"

    def test_extracts_author(self, sample_soup):
        metadata = extract_metadata(sample_soup, "https://plato.stanford.edu/entries/consciousness/")
        assert metadata["author"] == "Robert Van Gulick"

    def test_extracts_published_date(self, sample_soup):
        metadata = extract_metadata(sample_soup, "https://plato.stanford.edu/entries/consciousness/")
        assert metadata["published"] == "2004-06-18"

    def test_extracts_revised_date(self, sample_soup):
        metadata = extract_metadata(sample_soup, "https://plato.stanford.edu/entries/consciousness/")
        assert metadata["revised"] == "2022-10-13"

    def test_includes_url(self, sample_soup):
        url = "https://plato.stanford.edu/entries/consciousness/"
        metadata = extract_metadata(sample_soup, url)
        assert metadata["url"] == url


class TestFormatFrontmatter:
    def test_formats_yaml(self):
        metadata = {
            "title": "Consciousness",
            "author": "Robert Van Gulick",
            "published": "2004-06-18",
            "revised": "2022-10-13",
            "url": "https://plato.stanford.edu/entries/consciousness/",
        }
        frontmatter = format_frontmatter(metadata)
        assert frontmatter.startswith("---\n")
        assert frontmatter.endswith("---\n")
        assert 'title: "Consciousness"' in frontmatter
        assert 'author: "Robert Van Gulick"' in frontmatter
