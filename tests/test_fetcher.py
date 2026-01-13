"""Tests for HTTP fetcher."""

import pytest

from sep_scraper.fetcher import fetch_article, validate_sep_url, ScraperError


class TestValidateSepUrl:
    def test_valid_url(self):
        url = "https://plato.stanford.edu/entries/consciousness/"
        assert validate_sep_url(url) == url

    def test_valid_url_without_trailing_slash(self):
        url = "https://plato.stanford.edu/entries/consciousness"
        assert validate_sep_url(url) == url

    def test_mirror_url(self):
        url = "https://seop.illc.uva.nl/entries/consciousness/"
        assert validate_sep_url(url) == url

    def test_invalid_domain(self):
        with pytest.raises(ValueError, match="Not a SEP URL"):
            validate_sep_url("https://example.com/entries/test/")

    def test_invalid_path(self):
        with pytest.raises(ValueError, match="Not an article URL"):
            validate_sep_url("https://plato.stanford.edu/about.html")


class TestFetchArticle:
    @pytest.mark.asyncio
    async def test_fetch_real_article(self):
        html = await fetch_article("https://plato.stanford.edu/entries/aristotle/")
        assert "<html" in html.lower()
        assert "Aristotle" in html

    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self):
        with pytest.raises(ScraperError):
            await fetch_article("https://plato.stanford.edu/entries/nonexistent-article-xyz/")
