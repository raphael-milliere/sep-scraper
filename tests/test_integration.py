"""Integration tests with real SEP articles."""

import pytest

from sep_scraper.cli import scrape_article


@pytest.mark.asyncio
@pytest.mark.integration
class TestRealArticles:
    async def test_aristotle_article(self):
        """Test with a standard article."""
        url = "https://plato.stanford.edu/entries/aristotle/"
        result = await scrape_article(url)

        # Check frontmatter
        assert result.startswith("---\n")
        assert "title:" in result
        assert "author:" in result
        assert "url:" in result

        # Check content structure
        assert "# " in result  # Has title
        assert "## " in result  # Has sections
        assert "## Bibliography" in result

    async def test_article_with_math(self):
        """Test with an article containing math."""
        url = "https://plato.stanford.edu/entries/aristotle-logic/"
        result = await scrape_article(url)

        # Should have converted math
        assert "$" in result  # Has math delimiters

    async def test_article_with_tables(self):
        """Test with an article that may have tables."""
        url = "https://plato.stanford.edu/entries/logic-modal/"
        result = await scrape_article(url)

        # Check basic structure
        assert result.startswith("---\n")
        assert "## Bibliography" in result


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_nonexistent_article(self):
        """Test handling of 404."""
        from sep_scraper.fetcher import ScraperError

        with pytest.raises(ScraperError):
            await scrape_article("https://plato.stanford.edu/entries/nonexistent-xyz-123/")
