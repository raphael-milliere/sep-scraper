"""Markdown assembler for SEP articles."""

from sep_scraper.metadata import format_frontmatter


def assemble_markdown(
    metadata: dict,
    content: str,
    footnotes: str,
    bibliography: str,
    appendices: list[tuple[str, str]] | None = None,
    preamble: str = "",
) -> str:
    """Assemble final markdown document from parts.

    Args:
        metadata: Article metadata dictionary
        content: Main article content as markdown
        footnotes: Formatted footnote definitions
        bibliography: Bibliography section as markdown
        appendices: Optional list of (title, content) tuples
        preamble: Optional introductory text before first section

    Returns:
        Complete markdown document
    """
    parts = []

    # YAML frontmatter
    parts.append(format_frontmatter(metadata))

    # Preamble (intro before first section)
    if preamble:
        parts.append(preamble)
        parts.append("")

    # Main content
    if content:
        parts.append(content)

    # Appendices
    if appendices:
        for title, appendix_content in appendices:
            parts.append("")
            parts.append(f"## Appendix {title}")
            parts.append("")
            parts.append(appendix_content)

    # Footnotes section
    if footnotes:
        parts.append("")
        parts.append("## Notes")
        parts.append("")
        parts.append(footnotes)

    # Bibliography
    if bibliography:
        parts.append("")
        parts.append(bibliography)

    return "\n".join(parts).strip() + "\n"
