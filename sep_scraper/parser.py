"""Main parser for SEP articles."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sep_scraper.converters import (
    TextConverter,
    MathConverter,
    FootnoteConverter,
    TableConverter,
    BibliographyConverter,
)
from sep_scraper.metadata import extract_metadata

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from bs4 import Tag


# Sections to exclude from main content
EXCLUDED_SECTIONS = {
    "related entries",
    "academic tools",
    "other internet resources",
    "acknowledgments",
}


class SEPParser:
    """Parse SEP article HTML and extract content."""

    def __init__(
        self,
        soup: BeautifulSoup,
        url: str,
        macros: dict[str, str] | None = None,
    ):
        """Initialize parser with parsed HTML.

        Args:
            soup: BeautifulSoup parsed document
            url: Source URL
            macros: Optional custom MathJax macros for expansion
        """
        self._soup = soup
        self._url = url
        self._text_converter = TextConverter()
        self._math_converter = MathConverter(macros)
        self._footnote_converter = FootnoteConverter(soup)
        self._table_converter = TableConverter()
        self._bib_converter = BibliographyConverter()

    def get_metadata(self) -> dict:
        """Extract article metadata.

        Returns:
            Dictionary with title, author, dates, url
        """
        return extract_metadata(self._soup, self._url)

    def get_main_content(self) -> str:
        """Extract and convert main article content.

        Returns:
            Markdown string of article body
        """
        main_text = self._soup.find("div", id="main-text")
        if not main_text:
            main_text = self._soup.find("div", id="aueditable")

        if not main_text:
            return ""

        lines = []
        skip_until_next_h2 = False

        for element in main_text.children:
            if not hasattr(element, "name"):
                continue

            # Check for section headings to exclude
            if element.name in ("h2", "h3"):
                heading_text = element.get_text(strip=True).lower()
                # Remove numbering for comparison
                heading_text = re.sub(r"^\d+\.\s*", "", heading_text)

                is_excluded = (
                    heading_text in EXCLUDED_SECTIONS
                    or heading_text in ("bibliography", "references")
                )

                if element.name == "h2":
                    # h2 always controls skip state
                    skip_until_next_h2 = is_excluded
                    if is_excluded:
                        continue
                else:  # h3
                    # h3 can start a skip, but never ends an existing skip
                    if is_excluded:
                        skip_until_next_h2 = True
                        continue
                    # Non-excluded h3 doesn't change skip state

            if skip_until_next_h2:
                continue

            # Convert element
            converted = self._convert_element(element)
            if converted:
                lines.append(converted)
                lines.append("")

        result = "\n".join(lines)

        # Convert math delimiters in the final text
        result = self._math_converter.convert_text(result)

        return result.strip()

    def _convert_element(self, element: Tag) -> str:
        """Convert a single HTML element to Markdown.

        Args:
            element: BeautifulSoup Tag

        Returns:
            Markdown string
        """
        if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return self._text_converter.convert(element)

        elif element.name == "p":
            return self._convert_paragraph(element)

        elif element.name in ("ul", "ol"):
            return self._text_converter.convert(element)

        elif element.name == "blockquote":
            return self._text_converter.convert(element)

        elif element.name == "table":
            return self._table_converter.convert(element)

        elif element.name == "div":
            # Recursively process div contents
            parts = []
            for child in element.children:
                if hasattr(child, "name"):
                    converted = self._convert_element(child)
                    if converted:
                        parts.append(converted)
            return "\n\n".join(parts)

        return ""

    def _convert_paragraph(self, element: Tag) -> str:
        """Convert paragraph with footnote and math handling.

        Args:
            element: p tag

        Returns:
            Markdown paragraph
        """
        result_parts = []

        for child in element.children:
            if isinstance(child, str):
                result_parts.append(child)
            elif child.name == "sup" and child.find("a"):
                # Footnote reference
                result_parts.append(self._footnote_converter.convert_reference(child))
            elif child.name == "script" and "math/tex" in child.get("type", ""):
                # Math element
                result_parts.append(self._math_converter.convert(child))
            elif child.name in ("span",) and child.get("class"):
                # Possible MathJax span
                if math_result := self._math_converter.extract_from_span(child):
                    result_parts.append(math_result)
                else:
                    result_parts.append(self._text_converter.convert_inline(child))
            else:
                result_parts.append(self._text_converter.convert_inline(child))

        text = "".join(result_parts)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def get_footnotes(self) -> str:
        """Get formatted footnote definitions.

        Returns:
            Markdown footnote definitions
        """
        return self._footnote_converter.format_definitions()

    def get_bibliography(self) -> str:
        """Extract and convert bibliography section.

        Returns:
            Markdown bibliography
        """
        # Find bibliography section
        for heading in self._soup.find_all(["h2", "h3"]):
            heading_text = heading.get_text(strip=True).lower()
            heading_text = re.sub(r"^\d+\.\s*", "", heading_text)

            if heading_text in ("bibliography", "references"):
                # Check if heading is in a dedicated section div
                section = heading.parent
                if (
                    section.name == "div"
                    and section.get("id") not in ("main-text", "aueditable")
                ):
                    return self._bib_converter.convert(section)

                # Build a virtual section from heading + following siblings
                section_html = str(heading)
                for sibling in heading.find_next_siblings():
                    if sibling.name in ("h2", "h3"):
                        break
                    section_html += str(sibling)

                temp_soup = BeautifulSoup(f"<div>{section_html}</div>", "lxml")
                return self._bib_converter.convert(temp_soup.div)

        return ""
