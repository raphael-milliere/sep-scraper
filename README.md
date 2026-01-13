# sep-scraper

Convert Stanford Encyclopedia of Philosophy articles to clean markdown.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Output to stdout
sep-scraper https://plato.stanford.edu/entries/consciousness/

# Save to file
sep-scraper https://plato.stanford.edu/entries/consciousness/ -o consciousness.md

# Save to directory (auto-named from entry)
sep-scraper https://plato.stanford.edu/entries/consciousness/ -d ./articles/
```

## Output

Generates markdown with YAML frontmatter:

```markdown
---
title: "Consciousness"
author: "Robert Van Gulick"
published: "2004-06-18"
revised: "2022-10-13"
url: "https://plato.stanford.edu/entries/consciousness/"
---

# Consciousness

Article content with inline math $x^2$ and display math:

$$\int_0^1 f(x) dx$$

## Bibliography

- Author, A., Year, *Title*, Publisher.

## Notes

[^1]: Footnote content.
```

## License

MIT
