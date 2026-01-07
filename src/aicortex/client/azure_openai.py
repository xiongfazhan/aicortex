"""Azure OpenAI client implementation.

Corresponds to src/client/azure_openai.rs in the Rust implementation.
"""

import httpx
import json
from typing import AsyncIterator
from .mod import Client, ChatCompletionsData, ChatCompletionsOutput, EmbeddingsData
from .stream import SseHandler, openai_chat_completions_streaming
from .model import Model


class AzureOpenAIClient(Client):
    """Azure OpenAI API client.

    Implements the Client interface for Azure OpenAI service.
    """

    def __init__(self, config: dict, model: Model):
        """Initialize Azure OpenAI client.

        Args:
            config: Client configuration (must contain api_base and api_key)
            model: Model to use
        """
        super().__init__(config, model)
        self.api_key = config.get("api_key") or ""
        self.api_base = config.get("api_base") or ""

        if not self.api_base:
            raise ValueError("api_base is required for Azure OpenAI")
        if not self.api_key:
            raise ValueError("api_key is required for Azure OpenAI")

    def _build_headers(self) -> dict[str, str]:
        """Build request headers.

        Returns:
            Headers dictionary (uses api-key header instead of Authorization)
        """
        return {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

    def _build_chat_body(self, data: ChatCompletionsData) -> dict:
        """Build chat completion request body.

        Args:
            data: Chat completion data

        Returns:
            Request body dictionary
        """
        body = {
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
        # Azure OpenAI URL format:
        # {api_base}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-12-01-preview
        deployment_name = self.model.name()
        url = f"{self.api_base}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-12-01-preview"

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
            Parsed chat completion output
        """
        text = ""
        tool_calls = []

        if "choices" in data and data["choices"]:
            choice = data["choices"][0]
            message = choice.get("message", {})

            # Get text content
            if "content" in message:
                text = message["content"] or ""

            # Get tool calls
            if "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    function = tool_call.get("function", {})
                    tool_calls.append({
                        "id": tool_call.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": function.get("name", ""),
                            "arguments": function.get("arguments", "{}"),
                        },
                    })

        # Get usage info
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")

        return ChatCompletionsOutput(
            text=text,
            tool_calls=tool_calls,
            id=data.get("id"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    async def chat_completions_streaming(
        self, data: ChatCompletionsData, handler: SseHandler
    ) -> None:
        """Make streaming chat completion request.

        Args:
            data: Chat completion data
            handler: SSE handler for streaming events
        """
        deployment_name = self.model.name()
        url = f"{self.api_base}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-12-01-preview"

        headers = self._build_headers()
        body = self._build_chat_body(data)

        async with self.http_client.stream("POST", url, headers=headers, json=body) as response:
            response.raise_for_status()
            await openai_chat_completions_streaming(response, handler)

    async def embeddings(
        self, data: EmbeddingsData
    ) -> list[list[float]]:
        """Make embeddings request.

        Args:
            data: Embeddings data

        Returns:
            List of embedding vectors
        """
        # Azure OpenAI URL format:
        # {api_base}/openai/deployments/{deployment_name}/embeddings?api-version=2024-10-21
        deployment_name = self.model.name()
        url = f"{self.api_base}/openai/deployments/{deployment_name}/embeddings?api-version=2024-10-21"

        headers = self._build_headers()
        body = {"input": data.texts}

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()

        # Extract embeddings from response
        embeddings = []
        if "data" in data:
            for item in data["data"]:
                embeddings.append(item.get("embedding", []))

        return embeddings


__all__ = ["AzureOpenAIClient"]
