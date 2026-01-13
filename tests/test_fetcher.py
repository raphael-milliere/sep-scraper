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


class TestFetchAppendices:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetches_multiple_appendices(self):
        from sep_scraper.fetcher import fetch_appendices

        # Use real SEP appendix URLs
        links = [
            ("https://plato.stanford.edu/entries/dynamic-epistemic/appendix-A-kripke.html", "A. Kripke models"),
            ("https://plato.stanford.edu/entries/dynamic-epistemic/appendix-C-relations.html", "C. Relations"),
        ]

        results = await fetch_appendices(links)

        assert len(results) == 2
        assert results[0][0] == "A. Kripke models"
        assert "<html" in results[0][1].lower()
        assert results[1][0] == "C. Relations"
        assert "<html" in results[1][1].lower()

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_input(self):
        from sep_scraper.fetcher import fetch_appendices

        results = await fetch_appendices([])

        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_skips_failed_fetches(self):
        from sep_scraper.fetcher import fetch_appendices

        links = [
            ("https://plato.stanford.edu/entries/dynamic-epistemic/appendix-A-kripke.html", "A. Kripke models"),
            ("https://plato.stanford.edu/entries/nonexistent/fake-appendix.html", "Fake appendix"),
        ]

        results = await fetch_appendices(links)

        # Should only return the successful fetch
        assert len(results) == 1
        assert results[0][0] == "A. Kripke models"
