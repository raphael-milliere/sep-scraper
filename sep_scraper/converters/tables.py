"""Table converter for SEP articles."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sep_scraper.converters.text import TextConverter

if TYPE_CHECKING:
    from bs4 import Tag


class TableConverter:
    """Convert HTML tables to Markdown tables."""

    def __init__(self):
        self._text_converter = TextConverter()

    def convert(self, table: Tag) -> str:
        """Convert an HTML table to Markdown.

        Args:
            table: BeautifulSoup table element

        Returns:
            Markdown table string
        """
        rows = []
        header_row = None
        body_rows = []

        # Find header row
        if thead := table.find("thead"):
            header_row = thead.find("tr")
        else:
            # First row with th cells is the header
            for tr in table.find_all("tr"):
                if tr.find("th"):
                    header_row = tr
                    break

        # Collect body rows
        if tbody := table.find("tbody"):
            body_rows = tbody.find_all("tr")
        else:
            # All rows except header
            for tr in table.find_all("tr"):
                if tr != header_row:
                    body_rows.append(tr)

        # Convert header
        if header_row:
            headers = [self._convert_cell(cell) for cell in header_row.find_all(["th", "td"])]
            rows.append("| " + " | ".join(headers) + " |")
            rows.append("|" + "|".join("---" for _ in headers) + "|")
        else:
            # No header - use first body row as header if we have rows
            if body_rows:
                first_row = body_rows.pop(0)
                cells = [self._convert_cell(cell) for cell in first_row.find_all(["td", "th"])]
                rows.append("| " + " | ".join(cells) + " |")
                rows.append("|" + "|".join("---" for _ in cells) + "|")

        # Convert body rows
        for tr in body_rows:
            cells = [self._convert_cell(cell) for cell in tr.find_all(["td", "th"])]
            if cells:
                rows.append("| " + " | ".join(cells) + " |")

        return "\n".join(rows)

    def _convert_cell(self, cell: Tag) -> str:
        """Convert a table cell to Markdown content.

        Args:
            cell: td or th element

        Returns:
            Cell content as Markdown string
        """
        # Convert inner content
        content = self._text_converter._convert_inline(cell)

        # Replace line breaks with space
        content = re.sub(r"\n+", " ", content)

        # Escape pipe characters
        content = content.replace("|", r"\|")

        # Normalize whitespace
        content = re.sub(r"\s+", " ", content).strip()

        return content
