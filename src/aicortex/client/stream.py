"""Stream handling for LLM responses.

Corresponds to src/client/stream.rs in the Rust implementation.
"""

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable, Optional, Any
import json


@dataclass
class SseEvent:
    """Server-Sent Event.

    Represents a single event from an SSE stream.
    """

    text: str = ""
    done: bool = False

    def is_text(self) -> bool:
        """Check if event contains text."""
        return bool(self.text)

    def is_done(self) -> bool:
        """Check if stream is done."""
        return self.done


@dataclass
class SseHandler:
    """Handler for SSE streaming responses.

    Receives text chunks from streaming API responses and manages
    the streaming state including abort signals.
    """

    sender: "asyncio.Queue[SseEvent]"
    abort_signal: Any = None
    buffer: str = ""
    tool_calls: list[Any] = field(default_factory=list)

    def __post_init__(self):
        """Initialize queue."""
        self.sender = asyncio.Queue()

    async def text(self, chunk: str) -> None:
        """Send a text chunk.

        Args:
            chunk: Text chunk to send
        """
        await self.sender.put(SseEvent(text=chunk))

    async def done(self) -> None:
        """Signal streaming is complete."""
        await self.sender.put(SseEvent(done=True))

    def abort(self) -> Any:
        """Get abort signal."""
        return self.abort_signal

    async def take(self) -> tuple[str, list[Any]]:
        """Take final results from stream.

        Returns:
            Tuple of (full_text, tool_calls)
        """
        return self.buffer, self.tool_calls


def parse_openai_sse(line: str) -> Optional[SseEvent]:
    """Parse OpenAI SSE line.

    Args:
        line: Raw SSE line (without "data: " prefix)

    Returns:
        Parsed event or None
    """
    if not line or line.strip() == "[DONE]":
        return SseEvent(done=True)

    try:
        data = json.loads(line)
        delta = data.get("choices", [{}])[0].get("delta", {})

        # Handle text content
        if "content" in delta:
            return SseEvent(text=delta["content"])

        # Handle tool calls (simplified)
        if "tool_calls" in delta:
            # In full implementation, would accumulate tool call chunks
            pass

    except json.JSONDecodeError:
        pass

    return None


async def iter_sse_lines(
    response: Any,
) -> AsyncIterator[str]:
    """Iterate over SSE lines from response.

    Args:
        response: HTTP response object

    Yields:
        SSE data lines (without "data: " prefix)
    """
    async for line in response.aiter_lines():
        line = line.strip()
        if line.startswith("data: "):
            yield line[6:]


async def openai_chat_completions_streaming(
    response: Any,
    handler: SseHandler,
) -> None:
    """Handle OpenAI streaming chat completion.

    Args:
        response: HTTP response
        handler: SSE handler to receive events
    """
    buffer = ""

    async for line in iter_sse_lines(response):
        event = parse_openai_sse(line)
        if event:
            if event.is_done():
                await handler.done()
                break
            if event.is_text():
                buffer += event.text
                await handler.text(event.text)

    # Store final results
    handler.buffer = buffer


__all__ = [
    "SseEvent",
    "SseHandler",
    "parse_openai_sse",
    "iter_sse_lines",
    "openai_chat_completions_streaming",
]
