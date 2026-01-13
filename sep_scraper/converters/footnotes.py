"""Footnote converter for SEP articles."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sep_scraper.converters.text import TextConverter

if TYPE_CHECKING:
    from bs4 import BeautifulSoup, Tag


class FootnoteConverter:
    """Extract and convert footnotes from SEP articles."""

    def __init__(self, soup: BeautifulSoup):
        """Initialize with parsed HTML document.

        Args:
            soup: BeautifulSoup parsed document
        """
        self._soup = soup
        self._text_converter = TextConverter()
        self._definitions: dict[str, str] = {}
        self._extract_definitions()

    def _extract_definitions(self) -> None:
        """Extract footnote definitions from the document."""
        # Look for notes section
        notes_section = None

        # Try finding by ID
        notes_section = self._soup.find("div", id=re.compile(r"note", re.I))

        # Try finding by heading
        if not notes_section:
            for heading in self._soup.find_all(["h2", "h3", "h4"]):
                if re.search(r"^notes?$", heading.get_text(strip=True), re.I):
                    notes_section = heading.parent
                    break

        if not notes_section:
            return

        # Extract each footnote
        for elem in notes_section.find_all(["p", "li"], id=re.compile(r"note|fn")):
            note_id = elem.get("id", "")
            # Extract number from ID
            match = re.search(r"(\d+)", note_id)
            if not match:
                continue

            num = match.group(1)

            # Get content, excluding back-reference link
            content_parts = []
            for child in elem.children:
                if hasattr(child, "name") and child.name == "a":
                    href = child.get("href", "")
                    if href.startswith("#ref") or child.get_text(strip=True) == "^":
                        continue
                if isinstance(child, str):
                    content_parts.append(child)
                elif hasattr(child, "name"):
                    content_parts.append(self._convert_element(child))

            content = "".join(content_parts).strip()
            self._definitions[num] = content

    def _convert_element(self, element: Tag) -> str:
        """Convert an inline element to Markdown, including its tag semantics.

        Args:
            element: BeautifulSoup Tag element

        Returns:
            Markdown string with proper formatting
        """
        inner = self._text_converter._convert_inline(element)
        if element.name in ("em", "i"):
            return f"*{inner}*"
        elif element.name in ("strong", "b"):
            return f"**{inner}**"
        elif element.name == "code":
            return f"`{inner}`"
        elif element.name == "a":
            href = element.get("href", "")
            return f"[{inner}]({href})"
        else:
            return inner

    def get_definitions(self) -> dict[str, str]:
        """Get all footnote definitions.

        Returns:
            Dict mapping footnote numbers to content
        """
        return self._definitions

    def convert_reference(self, element: Tag) -> str:
        """Convert a footnote reference to Markdown syntax.

        Args:
            element: sup element containing footnote link

        Returns:
            Markdown footnote reference like [^1]
        """
        # Find the anchor inside
        anchor = element.find("a")
        if not anchor:
            return element.get_text(strip=True)

        href = anchor.get("href", "")

        # Extract number from href or text
        if match := re.search(r"(\d+)", href):
            num = match.group(1)
        elif match := re.search(r"(\d+)", anchor.get_text()):
            num = match.group(1)
        else:
            return element.get_text(strip=True)

        return f"[^{num}]"

    def format_definitions(self) -> str:
        """Format all footnote definitions as Markdown.

        Returns:
            Markdown footnote definitions block
        """
        if not self._definitions:
            return ""

        lines = []
        for num in sorted(self._definitions.keys(), key=int):
            content = self._definitions[num]
            # Handle multiline content
            content_lines = content.split("\n\n")
            if len(content_lines) > 1:
                lines.append(f"[^{num}]: {content_lines[0]}")
                for extra_line in content_lines[1:]:
                    lines.append(f"    {extra_line}")
            else:
                lines.append(f"[^{num}]: {content}")
            lines.append("")  # Blank line between footnotes

        return "\n".join(lines).rstrip()
