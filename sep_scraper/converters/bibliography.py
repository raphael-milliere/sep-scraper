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

        # Find and convert heading
        heading = section.find(["h2", "h3", "h4"])
        if heading:
            heading_text = heading.get_text(strip=True)
            lines.append(f"## {heading_text}")
            lines.append("")

        # Try list-based bibliography first
        if ul := section.find("ul"):
            for li in ul.find_all("li", recursive=False):
                entry = self._text_converter.convert_inline(li)
                lines.append(f"- {entry}")
                lines.append("")
        # Fall back to paragraph-based
        else:
            for p in section.find_all("p"):
                entry = self._text_converter.convert_inline(p)
                if entry:
                    lines.append(entry)
                    lines.append("")

        return "\n".join(lines).rstrip()
