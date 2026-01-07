"""Claude API client.

Corresponds to src/client/claude.rs in the Rust implementation.
"""

import json
from typing import AsyncIterator, Optional

from .mod import Client, ChatCompletionsData, ChatCompletionsOutput
from .stream import SseHandler, parse_openai_sse
from .model import Model
from ..utils import strip_think_tag


class ClaudeClient(Client):
    """Claude API client.

    Implements the Client interface for Anthropic's Claude API.
    """

    API_BASE = "https://api.anthropic.com/v1"

    def __init__(self, config: dict, model: Model):
        """Initialize Claude client.

        Args:
            config: Client configuration
            model: Model to use
        """
        super().__init__(config, model)
        self.api_key = config.get("api_key") or ""
        self.api_base = config.get("api_base") or self.API_BASE

    def _build_headers(self) -> dict[str, str]:
        """Build request headers.

        Returns:
            Headers dictionary
        """
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _build_chat_body(self, data: ChatCompletionsData) -> dict:
        """Build chat completion request body for Claude.

        Args:
            data: Chat completion data

        Returns:
            Request body dictionary
        """
        from .message import extract_system_message

        messages = data.messages.copy()
        system_message = extract_system_message(messages)

        # Build messages array
        claude_messages = []
        network_image_urls = []

        for i, message in enumerate(messages):
            role = message.role.value
            content = message.content

            if isinstance(content, str):
                text = content
                # Strip thinking tags from assistant messages (except last)
                if message.role.is_assistant() and i < len(messages) - 1:
                    text = strip_think_tag(text)
                claude_messages.append({"role": role, "content": text})

            elif isinstance(content, list):
                content_list = []
                for part in content:
                    if part.type == "text":
                        content_list.append({"type": "text", "text": part.text})
                    elif part.type == "image_url":
                        url = part.image_url.url
                        # Handle base64 images
                        if url.startswith("data:"):
                            media_type, base64_data = url.split(";", 1)[1].split(",", 1)
                            content_list.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_data,
                                },
                            })
                        else:
                            network_image_urls.append(url)
                            content_list.append({"type": "image", "source": {"type": "url", "url": url}})

                if content_list:
                    claude_messages.append({"role": role, "content": content_list})

        body = {
            "model": self.model.name(),
            "messages": claude_messages,
            "stream": data.stream,
        }

        if system_message:
            body["system"] = system_message

        if data.temperature is not None:
            body["temperature"] = data.temperature
        if data.top_p is not None:
            body["top_p"] = data.top_p
        if data.max_tokens is not None:
            body["max_tokens"] = data.max_tokens

        return body

    async def chat_completions(
        self, data: ChatCompletionsData
    ) -> ChatCompletionsOutput:
        """Make non-streaming chat completion request.

        Args:
            data: Chat completion data

        Returns:
            Chat completion output
        """
        url = f"{self.api_base.rstrip('/')}/messages"
        headers = self._build_headers()
        body = self._build_chat_body(data)

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        return self._parse_chat_response(response.json())

    def _parse_chat_response(self, data: dict) -> ChatCompletionsOutput:
        """Parse Claude chat completion response.

        Args:
            data: Response JSON data

        Returns:
            Parsed output
        """
        content_block = data.get("content", [])
        text_parts = []
        tool_calls = []

        for block in content_block:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "type": "function",
                    "function": {
                        "name": block.get("name"),
                        "arguments": block.get("input", {}),
                    },
                    "id": block.get("id"),
                })

        return ChatCompletionsOutput(
            text="".join(text_parts),
            tool_calls=tool_calls,
            id=data.get("id"),
            input_tokens=data.get("usage", {}).get("input_tokens"),
            output_tokens=data.get("usage", {}).get("output_tokens"),
        )

    async def chat_completions_streaming(
        self, data: ChatCompletionsData
    ) -> AsyncIterator[str]:
        """Make streaming chat completion request.

        Args:
            data: Chat completion data

        Yields:
            Response text chunks
        """
        url = f"{self.api_base.rstrip('/')}/messages"
        headers = self._build_headers()
        body = self._build_chat_body(data)
        body["stream"] = True

        async with self.http_client.stream("POST", url, headers=headers, json=body) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.strip().startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                        event_type = event.get("type")

                        if event_type == "content_block_start":
                            # Handle tool use start
                            if event.get("content_block", {}).get("type") == "tool_use":
                                pass  # Tool use will be assembled

                        elif event_type == "content_block_delta":
                            delta = event.get("delta", {})
                            if "text" in delta:
                                yield delta["text"]
                            elif "thinking" in delta:
                                # Thinking content
                                pass

                        elif event_type == "content_block_stop":
                            pass

                    except json.JSONDecodeError:
                        continue

    async def embeddings(self, data) -> list[list[float]]:
        """Claude does not support embeddings.

        Args:
            data: Embedding data

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Claude does not support embeddings")

    async def rerank(self, data) -> list:
        """Claude does not support reranking.

        Args:
            data: Rerank data

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Claude does not support reranking")


__all__ = ["ClaudeClient"]
