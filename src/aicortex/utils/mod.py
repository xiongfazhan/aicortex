"""General utility functions.

Corresponds to src/utils/mod.rs in the Rust implementation.
"""

import re
from typing import Optional

# Think tag pattern for Claude models
THINK_TAG_RE = re.compile(r"<thinking>.*?</thinking>", re.DOTALL)


def estimate_token_length(text: str) -> int:
    """Estimate token count for text.

    Approximation: 1 token ≈ 4 characters for English text.
    This is a rough estimate suitable for quick calculations.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Rough approximation: 1 token per 4 characters
    return len(text) // 4


def strip_think_tag(text: str) -> str:
    """Remove Claude thinking tags from text.

    Args:
        text: Text potentially containing <thinking> tags

    Returns:
        Text with thinking tags removed
    """
    return THINK_TAG_RE.sub("", text)


def extract_code_block(text: str) -> str:
    """Extract code block from markdown text.

    Args:
        text: Markdown text possibly containing code blocks

    Returns:
        Extracted code, or original text if no code block found
    """
    # Try to extract code from ```code``` blocks
    match = re.search(r"```(?:\w+)?\n([\s\S]+?)```", text)
    if match:
        return match.group(1)
    return text


def fuzzy_filter(items: list[str], query: str) -> list[str]:
    """Filter items using fuzzy matching.

    Args:
        items: List of items to filter
        query: Query string

    Returns:
        Filtered and sorted list of items
    """
    if not query:
        return items

    query_lower = query.lower()

    # Exact match gets highest priority
    exact_matches = [item for item in items if item.lower() == query_lower]
    if exact_matches:
        return exact_matches

    # Prefix match
    prefix_matches = [item for item in items if item.lower().startswith(query_lower)]
    if prefix_matches:
        return prefix_matches

    # Substring match
    substring_matches = [item for item in items if query_lower in item.lower()]
    if substring_matches:
        return substring_matches

    # Use fuzzy matching if available
    try:
        from thefuzz import fuzz, process

        results = process.extract(query, items, limit=10, scorer=fuzz.WRatio)
        return [item for item, score in results if score > 60]
    except ImportError:
        # Fallback to simple contains
        return [item for item in items if query_lower in item.lower()]


def pretty_error(err: Exception) -> str:
    """Format an exception for display.

    Args:
        err: Exception to format

    Returns:
        Formatted error message
    """
    return f"Error: {err}"


def temp_file(suffix: str, prefix: str = "") -> str:
    """Create a temporary file path.

    Args:
        suffix: File suffix/extension
        prefix: Optional prefix for the filename

    Returns:
        Path to temporary file
    """
    import tempfile

    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    import os

    os.close(fd)
    return path


def is_url(text: str) -> bool:
    """Check if text is a URL.

    Args:
        text: Text to check

    Returns:
        True if text appears to be a URL
    """
    return text.startswith(("http://", "https://"))


def set_proxy(url: Optional[str]) -> dict[str, str]:
    """Set proxy configuration for HTTP clients.

    Args:
        url: Proxy URL or None

    Returns:
        Dictionary with proxy configuration
    """
    if not url:
        return {}
    return {"http://": url, "https://": url}


__all__ = [
    "estimate_token_length",
    "strip_think_tag",
    "extract_code_block",
    "fuzzy_filter",
    "pretty_error",
    "temp_file",
    "is_url",
    "set_proxy",
]
