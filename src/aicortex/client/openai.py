"""OpenAI client implementation.

Corresponds to src/client/openai.rs in the Rust implementation.
"""

import httpx
import json
from typing import AsyncIterator
from .mod import Client, ChatCompletionsData, ChatCompletionsOutput, EmbeddingsData
from .stream import SseHandler, openai_chat_completions_streaming
from .model import Model


class OpenAIClient(Client):
    """OpenAI API client.

    Implements the Client interface for OpenAI and OpenAI-compatible APIs.
    """

    API_BASE = "https://api.openai.com/v1"

    def __init__(self, config: dict, model: Model):
        """Initialize OpenAI client.

        Args:
            config: Client configuration
            model: Model to use
        """
        super().__init__(config, model)
        self.api_key = config.get("api_key") or ""
        self.api_base = config.get("api_base") or self.API_BASE
        self.organization_id = config.get("organization_id")

    def _build_headers(self) -> dict[str, str]:
        """Build request headers.

        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id
        return headers

    def _build_chat_body(self, data: ChatCompletionsData) -> dict:
        """Build chat completion request body.

        Args:
            data: Chat completion data

        Returns:
            Request body dictionary
        """
        body = {
            "model": self.model.name(),
            "messages": [msg.to_dict() for msg in data.messages],
            "stream": data.stream,
        }

        if data.temperature is not None:
            body["temperature"] = data.temperature
        if data.top_p is not None:
            body["top_p"] = data.top_p
        if data.functions:
            body["tools"] = [
                {"type": "function", "function": fn} for fn in data.functions
            ]

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
        url = f"{self.api_base}/chat/completions"
        headers = self._build_headers()
        body = self._build_chat_body(data)

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        return self._parse_chat_response(response.json())

    def _parse_chat_response(self, data: dict) -> ChatCompletionsOutput:
        """Parse chat completion response.

        Args:
            data: Response JSON data

        Returns:
            Parsed output
        """
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        text = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        return ChatCompletionsOutput(
            text=text,
            tool_calls=tool_calls,
            id=data.get("id"),
            input_tokens=data.get("usage", {}).get("prompt_tokens"),
            output_tokens=data.get("usage", {}).get("completion_tokens"),
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
        url = f"{self.api_base}/chat/completions"
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
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    async def embeddings(self, data: EmbeddingsData) -> list[list[float]]:
        """Make embedding request.

        Args:
            data: Embedding data

        Returns:
            List of embedding vectors
        """
        url = f"{self.api_base}/embeddings"
        headers = self._build_headers()
        body = {
            "model": self.model.name(),
            "input": data.texts,
        }

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        result = response.json()
        return [item["embedding"] for item in result.get("data", [])]


__all__ = ["OpenAIClient"]
