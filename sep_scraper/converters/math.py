"""Math/LaTeX converter for SEP articles."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bs4 import Tag


class MathConverter:
    """Convert MathJax/LaTeX elements to Markdown math syntax."""

    def __init__(self, macros: dict[str, tuple[str, int]] | None = None):
        """Initialize converter with optional custom macros.

        Args:
            macros: Dictionary mapping macro names to (expansion, num_args) tuples
        """
        self._macros = macros or {}

    def _extract_brace_arg(self, text: str, start: int) -> tuple[str, int] | None:
        """Extract a brace-delimited argument from text, handling nesting.

        Args:
            text: The text to extract from
            start: Position where '{' should be

        Returns:
            Tuple of (argument_content, end_position) or None if no valid arg
        """
        if start >= len(text) or text[start] != "{":
            return None

        depth = 1
        pos = start + 1
        while pos < len(text) and depth > 0:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            elif text[pos] == "\\" and pos + 1 < len(text):
                # Skip escaped character
                pos += 1
            pos += 1

        if depth != 0:
            return None

        # Extract content between braces
        content = text[start + 1 : pos - 1]
        return (content, pos)

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
        for _ in range(5):  # Max 5 passes for nested expansion
            changed = False
            for name, (expansion, num_args) in self._macros.items():
                if num_args == 0:
                    # Simple replacement: \macroname -> expansion
                    pattern = re.escape("\\") + name + r"(?![a-zA-Z])"
                    new_result = re.sub(pattern, lambda m: expansion, result)
                    if new_result != result:
                        changed = True
                        result = new_result
                else:
                    # Macro with arguments: \macroname{arg1}{arg2}...
                    # Need to find and replace each occurrence manually
                    new_result = self._expand_macro_with_args(
                        result, name, expansion, num_args
                    )
                    if new_result != result:
                        changed = True
                        result = new_result
            if not changed:
                break

        return result

    def _expand_macro_with_args(
        self, text: str, name: str, expansion: str, num_args: int
    ) -> str:
        """Expand a single macro with arguments throughout the text.

        Args:
            text: Text to process
            name: Macro name (without backslash)
            expansion: Expansion template with #1, #2, etc.
            num_args: Number of arguments expected

        Returns:
            Text with macro expanded
        """
        result = []
        pos = 0
        pattern = re.compile(re.escape("\\") + name + r"(?![a-zA-Z])")

        while pos < len(text):
            match = pattern.search(text, pos)
            if not match:
                result.append(text[pos:])
                break

            # Add text before the match
            result.append(text[pos : match.start()])

            # Try to extract arguments
            arg_pos = match.end()
            args = []
            success = True

            for _ in range(num_args):
                # Skip whitespace before argument
                while arg_pos < len(text) and text[arg_pos] in " \t\n":
                    arg_pos += 1

                extracted = self._extract_brace_arg(text, arg_pos)
                if extracted is None:
                    success = False
                    break
                arg_content, arg_pos = extracted
                args.append(arg_content)

            if success and len(args) == num_args:
                # Substitute arguments into expansion
                expanded = expansion
                for i, arg in enumerate(args, 1):
                    expanded = expanded.replace(f"#{i}", arg)
                result.append(expanded)
                pos = arg_pos
            else:
                # Couldn't extract args, keep original and move past macro name
                result.append(text[match.start() : match.end()])
                pos = match.end()

        return "".join(result)

    def _convert_eqref(self, text: str) -> str:
        """Convert \\eqref{X} to (X) for KaTeX compatibility.

        Since \\eqref often appears in running text (outside math mode),
        we convert it to a simple parenthesized reference.

        Args:
            text: Text containing \\eqref references

        Returns:
            Text with eqref converted to parenthesized format
        """
        return re.sub(r"\\eqref\{([^}]+)\}", r"(\1)", text)

    def _convert_mbox(self, text: str) -> str:
        """Convert \\mbox{...} to \\text{...} for KaTeX compatibility.

        KaTeX doesn't support \\mbox, but \\text provides equivalent functionality.

        Args:
            text: Text containing \\mbox commands

        Returns:
            Text with mbox converted to text
        """
        return re.sub(r"\\mbox\{", r"\\text{", text)

    def _normalize_display_math(self, text: str) -> str:
        """Normalize display math blocks for KaTeX compatibility.

        - Removes leading whitespace from $$ delimiters
        - Consolidates multi-line display math content

        Args:
            text: Text with display math blocks

        Returns:
            Text with normalized display math
        """

        def normalize_block(match: re.Match) -> str:
            content = match.group(1)
            # Normalize internal whitespace while preserving structure
            # Remove leading/trailing whitespace from each line
            lines = [line.strip() for line in content.strip().split("\n")]
            # Filter empty lines and rejoin
            lines = [line for line in lines if line]
            normalized = " ".join(lines)
            return f"$$\n{normalized}\n$$"

        # Match display math blocks, including any leading whitespace on the line
        # This ensures $$ starts at the beginning of a line
        return re.sub(
            r"^[ \t]*\$\$(.*?)\$\$",
            normalize_block,
            text,
            flags=re.DOTALL | re.MULTILINE,
        )

    def _normalize_inline_math(self, text: str) -> str:
        """Normalize inline math blocks to single lines.

        Joins inline math ($...$) that spans multiple lines into single lines
        for better compatibility with KaTeX renderers.

        Args:
            text: Text with potentially multi-line inline math

        Returns:
            Text with inline math normalized to single lines
        """

        def normalize_match(match: re.Match) -> str:
            content = match.group(1)
            # Replace newlines and collapse whitespace
            content = re.sub(r"\s+", " ", content)
            return f"${content}$"

        # Match inline math (single $, not $$)
        # Use negative lookbehind/lookahead to avoid matching $$
        return re.sub(
            r"(?<!\$)\$(?!\$)((?:[^$]|\\\$)+?)(?<!\$)\$(?!\$)",
            normalize_match,
            text,
            flags=re.DOTALL,
        )

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
        - \\eqref{X} -> \\text{(X)}
        - Multi-line inline math -> single line

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

        # Convert \eqref{X} to (X) for KaTeX compatibility
        text = self._convert_eqref(text)

        # Convert \mbox{} to \text{} for KaTeX compatibility
        text = self._convert_mbox(text)

        # Normalize display math (remove indentation, consolidate lines)
        text = self._normalize_display_math(text)

        # Normalize inline math to single lines
        text = self._normalize_inline_math(text)

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
