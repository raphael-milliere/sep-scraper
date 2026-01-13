"""Markdown assembler for SEP articles."""

from sep_scraper.metadata import format_frontmatter


def assemble_markdown(
    metadata: dict,
    content: str,
    footnotes: str,
    bibliography: str,
) -> str:
    """Assemble final markdown document from parts.

    Args:
        metadata: Article metadata dictionary
        content: Main article content as markdown
        footnotes: Formatted footnote definitions
        bibliography: Bibliography section as markdown

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
