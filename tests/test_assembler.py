"""Tests for markdown assembler."""

import pytest

from sep_scraper.assembler import assemble_markdown


class TestAssembleMarkdown:
    def test_basic_assembly(self):
        metadata = {
            "title": "Test Article",
            "author": "Test Author",
            "published": "2024-01-01",
            "revised": "2024-01-01",
            "url": "https://plato.stanford.edu/entries/test/",
        }
        content = "This is the article content."
        footnotes = "[^1]: A footnote."
        bibliography = "## Bibliography\n\n- Entry 1"

        result = assemble_markdown(metadata, content, footnotes, bibliography)

        # Check structure
        assert result.startswith("---\n")
        assert "title: " in result
        assert "# Test Article" in result
        assert "This is the article content." in result
        assert "## Notes" in result
        assert "[^1]: A footnote." in result
        assert "## Bibliography" in result

    def test_without_footnotes(self):
        metadata = {"title": "Test", "author": None, "published": None, "revised": None, "url": ""}
        content = "Content"

        result = assemble_markdown(metadata, content, "", "")

        assert "## Notes" not in result

    def test_without_bibliography(self):
        metadata = {"title": "Test", "author": None, "published": None, "revised": None, "url": ""}
        content = "Content"
        footnotes = "[^1]: Note"

        result = assemble_markdown(metadata, content, footnotes, "")

        assert "## Notes" in result
        assert "## Bibliography" not in result

    def test_proper_section_order(self):
        metadata = {"title": "Test", "author": None, "published": None, "revised": None, "url": ""}
        content = "Main content"
        footnotes = "[^1]: Note"
        bibliography = "## Bibliography\n\n- Entry"

        result = assemble_markdown(metadata, content, footnotes, bibliography)

        # Find positions
        content_pos = result.find("Main content")
        notes_pos = result.find("## Notes")
        bib_pos = result.find("## Bibliography")

        assert content_pos < notes_pos < bib_pos
