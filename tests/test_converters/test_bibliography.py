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


class TestHierarchicalBibliography:
    def test_multiple_sections_with_headings(self, converter):
        """Test bibliography with h3 sections and multiple ul lists."""
        html = """
        <div>
            <h2>Bibliography</h2>
            <h3>A. Primary Sources</h3>
            <ul>
                <li>Source 1</li>
                <li>Source 2</li>
            </ul>
            <h3>B. Secondary Literature</h3>
            <ul>
                <li>Article 1</li>
                <li>Article 2</li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.div)

        assert "## Bibliography" in result
        assert "### A. Primary Sources" in result
        assert "- Source 1" in result
        assert "- Source 2" in result
        assert "### B. Secondary Literature" in result
        assert "- Article 1" in result
        assert "- Article 2" in result

    def test_h4_subsections(self, converter):
        """Test bibliography with h3 and h4 nested headings."""
        html = """
        <div>
            <h2>Bibliography</h2>
            <h3>A. Primary Sources</h3>
            <h4>1. Commentaries</h4>
            <ul>
                <li>Commentary 1</li>
            </ul>
            <h4>2. Treatises</h4>
            <ul>
                <li>Treatise 1</li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.div)

        assert "### A. Primary Sources" in result
        assert "#### 1. Commentaries" in result
        assert "- Commentary 1" in result
        assert "#### 2. Treatises" in result
        assert "- Treatise 1" in result

    def test_nested_list_entries(self, converter):
        """Test bibliography entries with nested sub-items."""
        html = """
        <div>
            <h2>Bibliography</h2>
            <ul>
                <li>Diels, H. (ed.), 1882, <em>Commentaria</em>, Berlin.
                    <ul>
                        <li>Vol. 1, <em>On Metaphysics</em>.</li>
                        <li>Vol. 2, <em>On Topics</em>.</li>
                    </ul>
                </li>
                <li>Smith, J., 2020, <em>Book</em>.</li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.div)

        assert "- Diels, H. (ed.), 1882, *Commentaria*, Berlin." in result
        assert "  - Vol. 1, *On Metaphysics*." in result
        assert "  - Vol. 2, *On Topics*." in result
        assert "- Smith, J., 2020, *Book*." in result