"""Markdown assembler for SEP articles."""

from sep_scraper.metadata import format_frontmatter


def assemble_markdown(
    metadata: dict,
    content: str,
    footnotes: str,
    bibliography: str,
    appendices: list[tuple[str, str]] | None = None,
) -> str:
    """Assemble final markdown document from parts.

    Args:
        metadata: Article metadata dictionary
        content: Main article content as markdown
        footnotes: Formatted footnote definitions
        bibliography: Bibliography section as markdown
        appendices: Optional list of (title, content) tuples

    Returns:
        Complete markdown document
    """
    parts = []

    # YAML frontmatter
    parts.append(format_frontmatter(metadata))

    # Title as H1
    if metadata.get("title"):
        parts.append(f"# {metadata['title']}")
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
