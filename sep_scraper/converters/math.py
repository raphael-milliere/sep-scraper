"""Math/LaTeX converter for SEP articles."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bs4 import Tag


class MathConverter:
    """Convert MathJax/LaTeX elements to Markdown math syntax."""

    def __init__(self, macros: dict[str, str] | None = None):
        """Initialize converter with optional custom macros.

        Args:
            macros: Dictionary mapping macro names to expansions
        """
        self._macros = macros or {}

    def _expand_macros(self, latex: str) -> str:
        """Expand custom macros in LaTeX string.

        Args:
            latex: LaTeX string with potential custom macros

        Returns:
            LaTeX string with macros expanded
        """
        if not self._macros:
            return latex

        result = latex
        # Expand macros - may need multiple passes for nested macros
        for _ in range(3):  # Max 3 passes for nested expansion
            changed = False
            for name, expansion in self._macros.items():
                # Match \macroname followed by non-letter or end of string
                # In raw f-string: \\\\ = two chars \\ = regex matches one backslash
                pattern = re.escape("\\") + name + r"(?![a-zA-Z])"
                # Use lambda to avoid backslash interpretation in replacement
                new_result = re.sub(pattern, lambda m: expansion, result)
                if new_result != result:
                    changed = True
                    result = new_result
            if not changed:
                break

        return result

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
        latex = self._expand_macros(latex)

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

        Also expands custom macros within math blocks.

        Args:
            text: Text containing LaTeX delimiters

        Returns:
            Text with Markdown math delimiters and expanded macros
        """
        # Convert display math \[...\] to $$...$$ with macro expansion
        def expand_display(match):
            latex = self._expand_macros(match.group(1))
            return f"$${latex}$$"

        text = re.sub(
            r"\\\[(.*?)\\\]",
            expand_display,
            text,
            flags=re.DOTALL,
        )

        # Convert inline math \(...\) to $...$ with macro expansion
        def expand_inline(match):
            latex = self._expand_macros(match.group(1))
            return f"${latex}$"

        text = re.sub(
            r"\\\((.*?)\\\)",
            expand_inline,
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
            latex = self._expand_macros(latex)
            return f"${latex}$"

        return None
