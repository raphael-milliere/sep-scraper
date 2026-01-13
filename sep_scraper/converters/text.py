"""Text element converter for basic HTML elements."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bs4 import Tag


class TextConverter:
    """Convert basic HTML text elements to Markdown."""

    def convert(self, element: Tag) -> str:
        """Convert an HTML element to Markdown.

        Args:
            element: BeautifulSoup Tag element

        Returns:
            Markdown string
        """
        tag_name = element.name

        if tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return self._convert_heading(element)
        elif tag_name == "p":
            return self._convert_paragraph(element)
        elif tag_name == "ul":
            return self._convert_list(element, ordered=False)
        elif tag_name == "ol":
            return self._convert_list(element, ordered=True)
        elif tag_name == "blockquote":
            return self._convert_blockquote(element)
        else:
            return self.convert_inline(element)

    def _convert_heading(self, element: Tag) -> str:
        """Convert heading element to Markdown."""
        level = int(element.name[1])
        prefix = "#" * level
        text = self.convert_inline(element)
        return f"{prefix} {text}"

    def _convert_paragraph(self, element: Tag) -> str:
        """Convert paragraph element to Markdown."""
        return self.convert_inline(element)

    def convert_inline(self, element: Tag) -> str:
        """Convert inline content to Markdown."""
        result = []

        for child in element.children:
            if isinstance(child, str):
                # Normalize whitespace
                text = re.sub(r"\s+", " ", child)
                result.append(text)
            elif child.name == "em" or child.name == "i":
                inner = self.convert_inline(child)
                result.append(f"*{inner}*")
            elif child.name == "strong" or child.name == "b":
                inner = self.convert_inline(child)
                result.append(f"**{inner}**")
            elif child.name == "a":
                text = self.convert_inline(child)
                href = child.get("href", "")
                # Skip creating links for anchors that only have id/name (no href)
                if href:
                    result.append(f"[{text}]({href})")
                else:
                    result.append(text)
            elif child.name == "sup":
                # Handle superscript (often footnotes)
                inner = self.convert_inline(child)
                result.append(inner)
            elif child.name == "sub":
                inner = self.convert_inline(child)
                result.append(inner)
            elif child.name == "br":
                result.append("\n")
            elif child.name == "code":
                inner = child.get_text()
                result.append(f"`{inner}`")
            elif hasattr(child, "children"):
                result.append(self.convert_inline(child))

        return "".join(result).strip()

    def _convert_list(self, element: Tag, ordered: bool, depth: int = 0) -> str:
        """Convert list element to Markdown."""
        lines = []
        indent = "  " * depth
        counter = 1

        for li in element.find_all("li", recursive=False):
            # Get direct text content (not nested lists)
            text_parts = []
            nested_list = None

            for child in li.children:
                if hasattr(child, "name") and child.name in ("ul", "ol"):
                    nested_list = child
                elif isinstance(child, str):
                    text_parts.append(child.strip())
                elif hasattr(child, "name"):
                    text_parts.append(self.convert_inline(child))

            text = " ".join(filter(None, text_parts))

            if ordered:
                lines.append(f"{indent}{counter}. {text}")
                counter += 1
            else:
                lines.append(f"{indent}- {text}")

            # Handle nested list
            if nested_list:
                nested_ordered = nested_list.name == "ol"
                nested_content = self._convert_list(nested_list, nested_ordered, depth + 1)
                lines.append(nested_content)

        return "\n".join(lines)

    def _convert_blockquote(self, element: Tag) -> str:
        """Convert blockquote element to Markdown."""
        lines = []

        for child in element.children:
            if hasattr(child, "name") and child.name == "p":
                text = self.convert_inline(child)
                lines.append(f"> {text}")
            elif isinstance(child, str) and child.strip():
                lines.append(f"> {child.strip()}")

        return "\n".join(lines)
