"""Tests for text converter."""

import pytest
from bs4 import BeautifulSoup

from sep_scraper.converters.text import TextConverter


@pytest.fixture
def converter():
    return TextConverter()


class TestHeadings:
    def test_h1(self, converter):
        html = "<h1>Title</h1>"
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.h1) == "# Title"

    def test_h2(self, converter):
        html = "<h2>Section</h2>"
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.h2) == "## Section"

    def test_h3(self, converter):
        html = "<h3>Subsection</h3>"
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.h3) == "### Subsection"


class TestParagraphs:
    def test_simple_paragraph(self, converter):
        html = "<p>This is a paragraph.</p>"
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.p) == "This is a paragraph."

    def test_paragraph_with_emphasis(self, converter):
        html = "<p>This is <em>emphasized</em> text.</p>"
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.p) == "This is *emphasized* text."

    def test_paragraph_with_strong(self, converter):
        html = "<p>This is <strong>bold</strong> text.</p>"
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.p) == "This is **bold** text."


class TestLinks:
    def test_simple_link(self, converter):
        html = '<p>See <a href="https://example.com">example</a>.</p>'
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.p) == "See [example](https://example.com)."

    def test_relative_link(self, converter):
        html = '<p>See <a href="../other-entry/">other entry</a>.</p>'
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.p)
        assert "[other entry](../other-entry/)" in result


class TestLists:
    def test_unordered_list(self, converter):
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.ul)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_ordered_list(self, converter):
        html = "<ol><li>First</li><li>Second</li></ol>"
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.ol)
        assert "1. First" in result
        assert "2. Second" in result

    def test_nested_list(self, converter):
        html = "<ul><li>Item 1<ul><li>Nested</li></ul></li></ul>"
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.ul)
        assert "- Item 1" in result
        assert "  - Nested" in result


class TestBlockquotes:
    def test_simple_blockquote(self, converter):
        html = "<blockquote><p>A quote.</p></blockquote>"
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.blockquote)
        assert result == "> A quote."

    def test_multiline_blockquote(self, converter):
        html = "<blockquote><p>Line 1.</p><p>Line 2.</p></blockquote>"
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.blockquote)
        assert "> Line 1." in result
        assert "> Line 2." in result
