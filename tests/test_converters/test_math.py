"""Tests for math converter."""

import pytest
from bs4 import BeautifulSoup

from sep_scraper.converters.math import MathConverter


@pytest.fixture
def converter():
    return MathConverter()


class TestScriptTagMath:
    def test_inline_math_script(self, converter):
        html = '<script type="math/tex">x^2 + y^2</script>'
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.script) == "$x^2 + y^2$"

    def test_display_math_script(self, converter):
        html = '<script type="math/tex; mode=display">\\int_0^1 f(x) dx</script>'
        soup = BeautifulSoup(html, "lxml")
        assert converter.convert(soup.script) == "$$\\int_0^1 f(x) dx$$"


class TestDelimiterMath:
    def test_inline_backslash_paren(self, converter):
        text = r"The formula \(x^2\) is quadratic."
        result = converter.convert_text(text)
        assert result == "The formula $x^2$ is quadratic."

    def test_display_backslash_bracket(self, converter):
        text = r"Consider: \[E = mc^2\]"
        result = converter.convert_text(text)
        assert result == "Consider: $$E = mc^2$$"

    def test_multiple_inline(self, converter):
        text = r"Given \(a\) and \(b\), compute \(a + b\)."
        result = converter.convert_text(text)
        assert result == "Given $a$ and $b$, compute $a + b$."


class TestAlignEnvironments:
    def test_align_block(self, converter):
        text = r"\[\begin{align} a &= b \\ c &= d \end{align}\]"
        result = converter.convert_text(text)
        assert "$$" in result
        assert r"\begin{align}" in result


class TestEdgeCases:
    def test_preserves_non_math_backslashes(self, converter):
        text = "Use \\n for newline."
        result = converter.convert_text(text)
        assert result == "Use \\n for newline."

    def test_empty_math(self, converter):
        text = r"Empty: \(\)"
        result = converter.convert_text(text)
        assert result == "Empty: $$"
