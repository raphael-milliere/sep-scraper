"""Tests for bibliography converter."""

import pytest
from bs4 import BeautifulSoup

from sep_scraper.converters.bibliography import BibliographyConverter


@pytest.fixture
def converter():
    return BibliographyConverter()


class TestListBibliography:
    def test_basic_list(self, converter):
        html = """
        <div>
            <h2>Bibliography</h2>
            <ul>
                <li>Smith, J., 2020. <em>A Great Book</em>, Publisher.</li>
                <li>Jones, A., 2019. "An Article", <em>Journal</em>, 1(2).</li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.div)
        assert "## Bibliography" in result
        assert "- Smith, J., 2020. *A Great Book*, Publisher." in result
        assert "- Jones, A., 2019." in result


class TestParagraphBibliography:
    def test_paragraph_entries(self, converter):
        html = """
        <div>
            <h2>References</h2>
            <p>Smith, J., 2020. <em>A Great Book</em>, Publisher.</p>
            <p>Jones, A., 2019. "An Article", <em>Journal</em>, 1(2).</p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.div)
        assert "## References" in result
        assert "Smith, J., 2020. *A Great Book*, Publisher." in result


class TestPreservation:
    def test_preserves_links(self, converter):
        html = """
        <div>
            <h2>Bibliography</h2>
            <ul>
                <li>Smith, J. <a href="https://doi.org/123">doi:123</a></li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.div)
        assert "[doi:123](https://doi.org/123)" in result

    def test_preserves_emphasis(self, converter):
        html = """
        <div>
            <h2>Bibliography</h2>
            <ul>
                <li><em>Italic Title</em> and <strong>Bold</strong>.</li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.div)
        assert "*Italic Title*" in result
        assert "**Bold**" in result
