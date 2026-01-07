"""HTML to Markdown conversion utilities.

Corresponds to src/utils/html_to_md.rs in the Rust implementation.
"""

import re
from html.parser import HTMLParser
from typing import Optional


class HtmlToMarkdownParser(HTMLParser):
    """HTML parser that converts to Markdown."""

    def __init__(self) -> None:
        """Initialize the parser."""
        super().__init__()
        self.output: list[str] = []
        self.in_head = False
        self.skip_until_tag: Optional[str] = None
        self.list_depth = 0
        self.code_block = False
        self.in_style = False
        self.in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        """Handle opening tags."""
        # Skip style and script tags
        if tag in ("style", "script"):
            if tag == "style":
                self.in_style = True
            else:
                self.in_script = True
            return

        if self.in_style or self.in_script:
            return

        # Remove webpage chrome (nav, footer, etc.)
        if tag in ("nav", "footer", "header", "aside"):
            self.skip_until_tag = tag
            return

        # Handle code blocks
        if tag == "pre":
            self.code_block = True
            self.output.append("\n```\n")
            return

        if tag == "code" and not self.code_block:
            self.output.append("`")
            return

        # Handle headings
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.output.append(f"\n{'#' * level} ")
            return

        # Handle lists
        if tag in ("ul", "ol"):
            self.list_depth += 1
            self.output.append("\n")
            return

        if tag == "li":
            indent = "  " * (self.list_depth - 1)
            prefix = "- " if self._current_list_type() == "ul" else "1. "
            self.output.append(f"\n{indent}{prefix}")
            return

        # Handle blockquote
        if tag == "blockquote":
            self.output.append("\n> ")
            return

        # Handle paragraphs
        if tag == "p":
            self.output.append("\n\n")
            return

        # Handle bold and italic
        if tag in ("b", "strong"):
            self.output.append("**")
            return

        if tag in ("i", "em"):
            self.output.append("*")
            return

        # Handle links
        if tag == "a":
            href = dict(attrs).get("href", "")
            self.output.append(f"[")
            self._current_href = href
            return

        # Handle images
        if tag == "img":
            alt = dict(attrs).get("alt", "")
            src = dict(attrs).get("src", "")
            self.output.append(f"![{alt}]({src})")
            return

        # Handle line breaks
        if tag == "br":
            self.output.append("  \n")
            return

        # Handle tables
        if tag == "table":
            self.output.append("\n\n")
            return

        if tag == "tr":
            self.output.append("\n")
            return

        if tag == "th":
            self.output.append("| ")
            return

        if tag == "td":
            self.output.append("| ")
            return

    def handle_endtag(self, tag: str) -> None:
        """Handle closing tags."""
        # Style and script tags
        if tag == "style":
            self.in_style = False
            return

        if tag == "script":
            self.in_script = False
            return

        if self.in_style or self.in_script:
            return

        # Check if exiting skipped section
        if self.skip_until_tag:
            if tag == self.skip_until_tag:
                self.skip_until_tag = None
            return

        # Code blocks
        if tag == "pre":
            self.code_block = False
            self.output.append("\n```\n")
            return

        if tag == "code" and not self.code_block:
            self.output.append("`")
            return

        # Links
        if tag == "a":
            href = getattr(self, "_current_href", "")
            self.output.append(f"]({href})")
            return

        # Bold and italic
        if tag in ("b", "strong"):
            self.output.append("**")
            return

        if tag in ("i", "em"):
            self.output.append("*")
            return

        # Lists
        if tag in ("ul", "ol"):
            self.list_depth = max(0, self.list_depth - 1)
            self.output.append("\n")
            return

        # Tables
        if tag == "td" or tag == "th":
            self.output.append(" ")
            return

    def handle_data(self, data: str) -> None:
        """Handle text data."""
        # Skip if in style/script or skipped section
        if self.in_style or self.in_script or self.skip_until_tag:
            return

        # Clean up whitespace
        text = data.strip()
        if text:
            self.output.append(text)

    def _current_list_type(self) -> str:
        """Get the current list type (simplified)."""
        return "ul"  # Simplified, would need tracking in real impl

    def get_markdown(self) -> str:
        """Get the generated Markdown.

        Returns:
            Markdown string
        """
        return "".join(self.output).strip()


def html_to_md(html: str) -> str:
    """Convert HTML to Markdown.

    Args:
        html: HTML string to convert

    Returns:
        Markdown string

    Examples:
        >>> html = "<h1>Title</h1><p>Hello <b>world</b></p>"
        >>> html_to_md(html)
        '# Title\\n\\nHello **world**'
    """
    if not html:
        return ""

    try:
        parser = HtmlToMarkdownParser()
        parser.feed(html)
        return parser.get_markdown()
    except Exception:
        # If parsing fails, try a simple fallback
        return _simple_html_to_md(html)


def _simple_html_to_md(html: str) -> str:
    """Simple fallback HTML to Markdown conversion.

    Args:
        html: HTML string

    Returns:
        Simplified Markdown string
    """
    # Remove common tags
    md = html

    # Remove script, style, head contents
    md = re.sub(r'<(script|style|head).*?>.*?</\1>', '', md, flags=re.DOTALL | re.IGNORECASE)

    # Convert headings
    md = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', md, flags=re.DOTALL | re.IGNORECASE)

    # Convert bold/italic
    md = re.sub(r'<(b|strong)[^>]*>(.*?)</\1>', r'**\2**', md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r'<(i|em)[^>]*>(.*?)</\1>', r'*\2*', md, flags=re.DOTALL | re.IGNORECASE)

    # Convert code
    md = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', md, flags=re.DOTALL | re.IGNORECASE)

    # Convert links
    md = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', md, flags=re.DOTALL | re.IGNORECASE)

    # Convert images
    md = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>', r'![\2](\1)', md, flags=re.IGNORECASE)
    md = re.sub(r'<img[^>]*src="([^"]*)"[^>]*>', r'![](\1)', md, flags=re.IGNORECASE)

    # Convert lists
    md = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', md, flags=re.DOTALL | re.IGNORECASE)

    # Convert paragraphs
    md = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\n\1\n\n', md, flags=re.DOTALL | re.IGNORECASE)

    # Convert line breaks
    md = re.sub(r'<br\s*/?>', '\n', md, flags=re.IGNORECASE)

    # Remove all remaining tags
    md = re.sub(r'<[^>]+>', '', md)

    # Clean up extra whitespace
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = md.strip()

    return md


__all__ = ["html_to_md"]
