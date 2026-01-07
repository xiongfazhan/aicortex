"""Render module.

Corresponds to src/render/mod.rs in the Rust implementation.
"""

import sys
from typing import AsyncIterator

from .markdown import MarkdownRender, RenderOptions, render_markdown
from .stream import (
    SseEvent,
    raw_stream,
    markdown_stream,
    render_stream,
    iter_sse_from_generator,
)


async def render_stream_async(
    events: AsyncIterator[SseEvent],
    highlight: bool = True,
    options: RenderOptions = None,
) -> None:
    """Render streaming events.

    Args:
        events: Async iterator of SSE events
        highlight: Whether to use syntax highlighting
        options: Render options (for markdown mode)
    """
    if options is None:
        options = RenderOptions()

    try:
        if highlight:
            await markdown_stream(events, options)
        else:
            await raw_stream(events)
    except KeyboardInterrupt:
        print()
        raise
    except Exception as e:
        render_error(e)
        raise


def render_error(err: Exception) -> None:
    """Render error to stderr.

    Args:
        err: Exception to render
    """
    sys.stderr.write(f"\x1b[31mError: {err}\x1b[0m\n")
    sys.stderr.flush()


__all__ = [
    "MarkdownRender",
    "RenderOptions",
    "render_markdown",
    "SseEvent",
    "raw_stream",
    "markdown_stream",
    "render_stream",
    "render_stream_async",
    "render_error",
    "iter_sse_from_generator",
]
