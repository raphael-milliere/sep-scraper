"""Tests for table converter."""

import pytest
from bs4 import BeautifulSoup

from sep_scraper.converters.tables import TableConverter


@pytest.fixture
def converter():
    return TableConverter()


class TestSimpleTables:
    def test_basic_table(self, converter):
        html = """
        <table>
            <thead><tr><th>A</th><th>B</th></tr></thead>
            <tbody><tr><td>1</td><td>2</td></tr></tbody>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.table)
        assert "| A | B |" in result
        assert "|---|---|" in result
        assert "| 1 | 2 |" in result

    def test_table_without_thead(self, converter):
        html = """
        <table>
            <tr><th>X</th><th>Y</th></tr>
            <tr><td>a</td><td>b</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.table)
        assert "| X | Y |" in result
        assert "| a | b |" in result


class TestCellContent:
    def test_cell_with_emphasis(self, converter):
        html = """
        <table>
            <tr><th>Term</th></tr>
            <tr><td><em>italic</em></td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.table)
        assert "*italic*" in result

    def test_cell_with_pipe_escaped(self, converter):
        html = """
        <table>
            <tr><th>Logic</th></tr>
            <tr><td>a | b</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.table)
        assert r"a \| b" in result

    def test_cell_with_linebreak(self, converter):
        html = """
        <table>
            <tr><th>Note</th></tr>
            <tr><td>Line 1<br/>Line 2</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.table)
        # Line breaks should become spaces or <br>
        assert "Line 1" in result and "Line 2" in result


class TestMultipleRows:
    def test_multiple_body_rows(self, converter):
        html = """
        <table>
            <tr><th>N</th><th>Square</th></tr>
            <tr><td>1</td><td>1</td></tr>
            <tr><td>2</td><td>4</td></tr>
            <tr><td>3</td><td>9</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")
        result = converter.convert(soup.table)
        lines = result.strip().split("\n")
        assert len(lines) == 5  # header + separator + 3 rows
