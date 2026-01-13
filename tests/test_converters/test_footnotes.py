"""Tests for footnote converter."""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from sep_scraper.converters.footnotes import FootnoteConverter


@pytest.fixture
def sample_soup():
    html_path = Path(__file__).parent.parent / "fixtures" / "sample_footnotes.html"
    html = html_path.read_text()
    return BeautifulSoup(html, "lxml")


@pytest.fixture
def converter(sample_soup):
    return FootnoteConverter(sample_soup)


class TestFootnoteExtraction:
    def test_extracts_footnote_definitions(self, converter):
        definitions = converter.get_definitions()
        assert "1" in definitions
        assert "2" in definitions

    def test_footnote_content(self, converter):
        definitions = converter.get_definitions()
        assert "First footnote content" in definitions["1"]
        assert "emphasis" in definitions["1"]

    def test_preserves_formatting_in_footnotes(self, converter):
        definitions = converter.get_definitions()
        assert "*emphasis*" in definitions["1"]


class TestFootnoteReferences:
    def test_converts_reference(self, converter):
        html = '<sup><a href="#note-1" id="ref-1">1</a></sup>'
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert_reference(soup.sup)
        assert result == "[^1]"

    def test_handles_different_id_formats(self, converter):
        html = '<sup><a href="#fn5">5</a></sup>'
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert_reference(soup.sup)
        assert result == "[^5]"


class TestFootnoteOutput:
    def test_formats_definitions_block(self, converter):
        output = converter.format_definitions()
        assert "[^1]:" in output
        assert "[^2]:" in output
        assert "First footnote content" in output

    def test_multiline_footnote_indentation(self, converter):
        # Footnotes with multiple paragraphs should be indented
        converter._definitions = {"1": "Line one.\n\nLine two."}
        output = converter.format_definitions()
        assert "[^1]: Line one." in output
        assert "    Line two." in output or "Line two." in output
