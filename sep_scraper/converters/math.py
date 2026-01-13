"""Math/LaTeX converter for SEP articles."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bs4 import Tag


class MathConverter:
    """Convert MathJax/LaTeX elements to Markdown math syntax."""

    def convert(self, element: Tag) -> str:
        """Convert a MathJax script tag to Markdown math.

        Args:
            element: BeautifulSoup Tag (script element with type="math/tex")

        Returns:
            Markdown math string with $ or $$ delimiters
        """
        if element.name != "script":
            return ""

        math_type = element.get("type", "")
        if "math/tex" not in math_type:
            return ""

        latex = element.string or ""
        latex = latex.strip()

        is_display = "mode=display" in math_type
        if is_display:
            return f"$${latex}$$"
        else:
            return f"${latex}$"

    def convert_text(self, text: str) -> str:
        """Convert LaTeX delimiters in text to Markdown math syntax.

        Handles:
        - \\(...\\) -> $...$
        - \\[...\\] -> $$...$$

        Args:
            text: Text containing LaTeX delimiters

        Returns:
            Text with Markdown math delimiters
        """
        # Convert display math \[...\] to $$...$$
        text = re.sub(
            r"\\\[(.*?)\\\]",
            r"$$\1$$",
            text,
            flags=re.DOTALL,
        )

        # Convert inline math \(...\) to $...$
        text = re.sub(
            r"\\\((.*?)\\\)",
            r"$\1$",
            text,
            flags=re.DOTALL,
        )

        return text

    def extract_from_span(self, element: Tag) -> str | None:
        """Extract LaTeX from MathJax-rendered span elements.

        Args:
            element: Span element that may contain MathJax output

        Returns:
            LaTeX string or None if not a math span
        """
        # Check for script tag inside
        if script := element.find("script", type=re.compile(r"math/tex")):
            return self.convert(script)

        # Check for data-latex attribute
        if latex := element.get("data-latex"):
            return f"${latex}$"

        return None
