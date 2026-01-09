"""Core LLM integration module.

Handles sending messages to LLMs and processing responses.
Corresponds to the core LLM interaction logic in the Rust implementation.
"""

# Fix Windows console encoding for UTF-8 output (must be first)
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
from typing import Any, Optional, AsyncIterator

from .client import (
    Client, Model, Message, MessageRole,
    ChatCompletionsData, ChatCompletionsOutput,
    OpenAIClient, ClaudeClient, GeminiClient, CohereClient,
    OpenAICompatibleClient, OPENAI_COMPATIBLE_PROVIDERS,
)
from .render import MarkdownRender, RenderOptions


class LLMCore:
    """Core LLM integration.

    Manages sending messages to LLMs and handling responses.
    """

    def __init__(
        self,
        client: Client,
        model: Model,
        stream: bool = True,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ):
        """Initialize LLM core.

        Args:
            client: LLM client instance
            model: Model to use
            stream: Whether to use streaming
            temperature: Temperature setting
            top_p: Top P setting
        """
        self.client = client
        self.model = model
        self.stream = stream
        self.temperature = temperature
        self.top_p = top_p
        self.last_response: Optional[str] = None

    async def send_message(
        self,
        message: str,
        messages: Optional[list[Message]] = None,
    ) -> str:
        """Send a message to the LLM.

        Args:
            message: User message
            messages: Optional message history

        Returns:
            LLM response text
        """
        # Build message list
        if messages is None:
            messages = []

        # Add current user message
        user_msg = Message.new(MessageRole.USER, message)
        messages.append(user_msg)

        # Create chat data
        chat_data = ChatCompletionsData(
            messages=messages,
            stream=self.stream,
            temperature=self.temperature,
            top_p=self.top_p,
        )

        # Call LLM
        if self.stream:
            response = await self._stream_response(chat_data)
        else:
            output = await self.client.chat_completions(chat_data)
            response = output.text

        # Store response
        self.last_response = response

        # Add assistant response to history
        assistant_msg = Message.new(MessageRole.ASSISTANT, response)
        messages.append(assistant_msg)

        return response

    async def _stream_response(self, chat_data: ChatCompletionsData) -> str:
        """Handle streaming response.

        Args:
            chat_data: Chat completion data

        Returns:
            Full response text
        """
        response_parts = []

        # Stream the response
        async for chunk in self.client.chat_completions_streaming(chat_data):
            response_parts.append(chunk)
            # Print chunk immediately for real-time feedback
            print(chunk, end="", flush=True)

        print()  # New line after streaming

        return "".join(response_parts)

    def get_last_response(self) -> Optional[str]:
        """Get the last response text.

        Returns:
            Last response or None
        """
        return self.last_response

    async def close(self) -> None:
        """Close the LLM client.

        Should be called when done with the LLM core.
        """
        if hasattr(self.client, "close"):
            await self.client.close()


async def create_client(
    client_type: str,
    api_key: str,
    model: Model,
    api_base: Optional[str] = None,
) -> Client:
    """Create an LLM client instance.

    Args:
        client_type: Type of client (openai, claude, gemini, cohere, nim, etc.)
        api_key: API key for the service
        model: Model to use
        api_base: Optional custom API base URL

    Returns:
        Client instance

    Raises:
        ValueError: If client type is unknown
    """
    config = {
        "api_key": api_key,
    }

    if not api_base:
        api_base = model.api_base()

    if api_base:
        config["api_base"] = api_base

    client_type_lower = client_type.lower()

    # Specialized clients
    match client_type_lower:
        case "openai":
            return OpenAIClient(config, model)
        case "claude" | "anthropic":
            return ClaudeClient(config, model)
        case "gemini":
            return GeminiClient(config, model)
        case "cohere":
            return CohereClient(config, model)

    # OpenAI-compatible providers (nim, nvidia, deepseek, groq, etc.)
    if client_type_lower in OPENAI_COMPATIBLE_PROVIDERS:
        # Use default API base from providers if not specified
        if not api_base:
            config["api_base"] = OPENAI_COMPATIBLE_PROVIDERS[client_type_lower]
        return OpenAICompatibleClient(config, model)

    raise ValueError(f"Unknown client type: {client_type}")


async def run_chat_completion(
    client: Client,
    messages: list[Message],
    stream: bool = True,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
) -> str:
    """Run a chat completion.

    Args:
        client: LLM client
        messages: Message list
        stream: Whether to stream response
        temperature: Temperature setting
        top_p: Top P setting

    Returns:
        Response text
    """
    chat_data = ChatCompletionsData(
        messages=messages,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
    )

    if stream:
        response_parts = []
        async for chunk in client.chat_completions_streaming(chat_data):
            response_parts.append(chunk)
            print(chunk, end="", flush=True)
        print()
        return "".join(response_parts)
    else:
        output = await client.chat_completions(chat_data)
        return output.text


__all__ = [
    "LLMCore",
    "create_client",
    "run_chat_completion",
]
