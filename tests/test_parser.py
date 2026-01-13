"""Tests for main parser."""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from sep_scraper.parser import SEPParser


@pytest.fixture
def sample_soup():
    html_path = Path(__file__).parent / "fixtures" / "sample_article.html"
    html = html_path.read_text()
    return BeautifulSoup(html, "lxml")


@pytest.fixture
def parser(sample_soup):
    return SEPParser(sample_soup, "https://plato.stanford.edu/entries/sample/")


class TestContentExtraction:
    def test_extracts_main_content(self, parser):
        content = parser.get_main_content()
        assert "First Section" in content
        assert "Content of first section" in content

    def test_excludes_related_entries(self, parser):
        content = parser.get_main_content()
        assert "Related Entries" not in content
        assert "Other Topic" not in content

    def test_excludes_academic_tools(self, parser):
        content = parser.get_main_content()
        assert "Academic Tools" not in content
        assert "How to cite" not in content


class TestMathConversion:
    def test_converts_inline_math(self, parser):
        content = parser.get_main_content()
        assert "$x^2$" in content


class TestFootnoteIntegration:
    def test_converts_footnote_references(self, parser):
        content = parser.get_main_content()
        assert "[^1]" in content

    def test_includes_footnote_definitions(self, parser):
        footnotes = parser.get_footnotes()
        assert "[^1]:" in footnotes


class TestTableConversion:
    def test_converts_tables(self, parser):
        content = parser.get_main_content()
        assert "| A | B |" in content


class TestBibliography:
    def test_extracts_bibliography(self, parser):
        bib = parser.get_bibliography()
        assert "## Bibliography" in bib
        assert "Author, A., 2024" in bib


class TestMetadata:
    def test_extracts_metadata(self, parser):
        metadata = parser.get_metadata()
        assert metadata["title"] == "Sample Topic"
        assert metadata["author"] == "Test Author"


class TestAppendixExtraction:
    def test_extracts_appendix_links(self):
        html = """
        <html><body>
        <div id="main-text">
            <h2>Appendices</h2>
            <ul>
                <li><a href="appendix-A.html">A. First appendix</a></li>
                <li><a href="appendix-B.html">B. Second appendix</a></li>
            </ul>
        </div>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = SEPParser(soup, "https://plato.stanford.edu/entries/test/")

        links = parser.get_appendix_links()

        assert len(links) == 2
        assert links[0] == ("https://plato.stanford.edu/entries/test/appendix-A.html", "A. First appendix")
        assert links[1] == ("https://plato.stanford.edu/entries/test/appendix-B.html", "B. Second appendix")

    def test_returns_empty_list_when_no_appendices(self):
        html = """
        <html><body>
        <div id="main-text">
            <h2>Introduction</h2>
            <p>Some content</p>
        </div>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = SEPParser(soup, "https://plato.stanford.edu/entries/test/")

        links = parser.get_appendix_links()

        assert links == []
