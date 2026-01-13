"""Tests for CLI interface."""

import pytest
from unittest.mock import patch, AsyncMock

from sep_scraper.cli import main, scrape_article


class TestScrapeArticle:
    @pytest.mark.asyncio
    async def test_returns_markdown(self):
        # This is an integration test - hits real SEP
        # Use a small, stable article
        url = "https://plato.stanford.edu/entries/aristotle/"
        result = await scrape_article(url)

        assert result.startswith("---\n")
        assert "title:" in result
        assert "# " in result


class TestCLI:
    def test_main_outputs_to_stdout(self, capsys):
        with patch("sep_scraper.cli.scrape_article") as mock:
            mock.return_value = "# Test Output\n\nContent."

            # Mock asyncio.run to return the mock value
            with patch("asyncio.run", return_value="# Test Output\n\nContent."):
                import sys
                old_argv = sys.argv
                sys.argv = ["sep-scraper", "https://plato.stanford.edu/entries/test/"]
                try:
                    main()
                except SystemExit:
                    pass
                finally:
                    sys.argv = old_argv

            captured = capsys.readouterr()
            assert "Test Output" in captured.out

    def test_invalid_url_exits_with_error(self):
        import sys
        old_argv = sys.argv
        sys.argv = ["sep-scraper", "https://example.com/invalid/"]
        try:
            with pytest.raises(SystemExit):
                main()
        finally:
            sys.argv = old_argv
