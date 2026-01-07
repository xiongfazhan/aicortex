"""Streaming output handling.

Corresponds to src/render/stream.rs in the Rust implementation.
"""

import asyncio
import sys
from dataclasses import dataclass
from typing import AsyncIterator, Callable, Optional

try:
    from prompt_toolkit import output
    from prompt_toolkit.application import Application
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.controls import FormattedTextControl
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from .markdown import MarkdownRender, RenderOptions


@dataclass
class SseEvent:
    """Server-Sent Event for streaming.

    Attributes:
        text: Text content
        done: Whether stream is complete
    """

    text: str = ""
    done: bool = False

    def is_text(self) -> bool:
        """Check if event contains text."""
        return bool(self.text)

    def is_done(self) -> bool:
        """Check if stream is done."""
        return self.done


async def raw_stream(events: AsyncIterator[SseEvent]) -> None:
    """Stream raw text output.

    Args:
        events: Async iterator of SSE events
    """
    async for event in events:
        if event.is_text():
            sys.stdout.write(event.text)
            sys.stdout.flush()
        if event.is_done():
            break


async def markdown_stream(
    events: AsyncIterator[SseEvent],
    options: RenderOptions,
) -> None:
    """Stream markdown with highlighting.

    Args:
        events: Async iterator of SSE events
        options: Render options
    """
    render = MarkdownRender(options)
    buffer = ""

    async for event in events:
        if event.is_text():
            text = event.text.replace("\t", "    ")
            buffer += text

            # Process complete lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                output = render.render_line(line + "\n")
                sys.stdout.write(output)
                sys.stdout.flush()

            # Render partial buffer
            if buffer:
                output = render.render_line(buffer)
                # Don't flush partial lines to avoid cursor jumping
                # We'll update in place if possible
                sys.stdout.write("\r" + " " * len(output) + "\r")
                sys.stdout.write(output)
                sys.stdout.flush()

        if event.is_done():
            # Print remaining buffer
            if buffer:
                output = render.render_line(buffer)
                sys.stdout.write(output + "\n")
                sys.stdout.flush()
            break


async def render_stream(
    events: AsyncIterator[SseEvent],
    highlight: bool = True,
    options: Optional[RenderOptions] = None,
) -> None:
    """Render streaming events.

    Args:
        events: Async iterator of SSE events
        highlight: Whether to use syntax highlighting
        options: Render options (for markdown mode)
    """
    if highlight and PROMPT_TOOLKIT_AVAILABLE:
        await markdown_stream(events, options or RenderOptions())
    else:
        await raw_stream(events)


async def iter_sse_from_generator(
    gen: AsyncIterator[str],
) -> AsyncIterator[SseEvent]:
    """Convert string generator to SSE events.

    Args:
        gen: Async iterator of strings

    Yields:
        SseEvent instances
    """
    async for chunk in gen:
        yield SseEvent(text=chunk)
    yield SseEvent(done=True)


__all__ = [
    "SseEvent",
    "raw_stream",
    "markdown_stream",
    "render_stream",
    "iter_sse_from_generator",
]
