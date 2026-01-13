"""Bibliography converter for SEP articles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sep_scraper.converters.text import TextConverter

if TYPE_CHECKING:
    from bs4 import Tag


class BibliographyConverter:
    """Convert bibliography sections to Markdown."""

    def __init__(self):
        self._text_converter = TextConverter()

    def convert(self, section: Tag) -> str:
        """Convert a bibliography section to Markdown.

        Args:
            section: Container element with bibliography content

        Returns:
            Markdown string with heading and entries
        """
        lines = []

        for element in section.children:
            if not hasattr(element, "name"):
                continue

            if element.name == "h2":
                heading_text = element.get_text(strip=True)
                lines.append(f"## {heading_text}")
                lines.append("")
            elif element.name == "h3":
                heading_text = element.get_text(strip=True)
                lines.append(f"### {heading_text}")
                lines.append("")
            elif element.name == "h4":
                heading_text = element.get_text(strip=True)
                lines.append(f"#### {heading_text}")
                lines.append("")
            elif element.name == "ul":
                list_md = self._convert_list(element, depth=0)
                lines.append(list_md)
                lines.append("")
            elif element.name == "p":
                entry = self._text_converter.convert_inline(element)
                if entry:
                    lines.append(entry)
                    lines.append("")

        return "\n".join(lines).rstrip()

    def _convert_list(self, ul: Tag, depth: int) -> str:
        """Convert a ul element to markdown list with proper nesting.

        Args:
            ul: The ul element to convert
            depth: Current nesting depth for indentation

        Returns:
            Markdown list string
        """
        lines = []
        indent = "  " * depth

        for li in ul.find_all("li", recursive=False):
            # Extract nested ul if present (temporarily remove for inline conversion)
            nested_ul = li.find("ul", recursive=False)
            if nested_ul:
                nested_ul.extract()

            # Convert the li content using TextConverter (handles em, strong, a, etc.)
            text = self._text_converter.convert_inline(li)
            # Normalize whitespace
            text = " ".join(text.split())

            if text:
                lines.append(f"{indent}- {text}")

            # Recurse for nested list
            if nested_ul:
                nested_md = self._convert_list(nested_ul, depth + 1)
                lines.append(nested_md)

        return "\n".join(lines)
