"""Cohere API client.

Corresponds to src/client/cohere.rs in the Rust implementation.
"""

import httpx
import json
from typing import AsyncIterator, Optional

from .mod import Client, ChatCompletionsData, ChatCompletionsOutput, EmbeddingsData, RerankData
from .model import Model


class CohereClient(Client):
    """Cohere API client.

    Implements the Client interface for Cohere's API.
    """

    API_BASE = "https://api.cohere.ai/v1"

    def __init__(self, config: dict, model: Model):
        """Initialize Cohere client.

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
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_chat_body(self, data: ChatCompletionsData) -> dict:
        """Build chat completion request body for Cohere.

        Args:
            data: Chat completion data

        Returns:
            Request body dictionary
        """
        # Build message history
        chat_history = []
        message = None

        for i, msg in enumerate(data.messages):
            if msg.role.is_user():
                if i == len(data.messages) - 1:
                    # Last user message is the query
                    message = msg.content if isinstance(msg.content, str) else ""
                else:
                    # Earlier user messages go to chat_history
                    content = msg.content if isinstance(msg.content, str) else ""
                    if content:
                        chat_history.append({"role": "USER", "message": content})
            elif msg.role.is_assistant():
                content = msg.content if isinstance(msg.content, str) else ""
                if content:
                    chat_history.append({"role": "CHATBOT", "message": content})

        body = {
            "message": message or "",
            "chat_history": chat_history,
        }

        if data.temperature is not None:
            body["temperature"] = data.temperature
        if data.top_p is not None:
            body["p"] = data.top_p

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
        url = f"{self.api_base}/chat"
        headers = self._build_headers()
        body = self._build_chat_body(data)

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        return self._parse_chat_response(response.json())

    def _parse_chat_response(self, data: dict) -> ChatCompletionsOutput:
        """Parse Cohere chat completion response.

        Args:
            data: Response JSON data

        Returns:
            Parsed output
        """
        text = data.get("text", "")

        # Cohere may return search results (citations)
        search_results = data.get("searchResults", [])
        documents = data.get("documents", [])

        return ChatCompletionsOutput(
            text=text,
            tool_calls=[],
            id=data.get("generation_id"),
            input_tokens=data.get("meta", {}).get("billed_units", {}).get("input_tokens"),
            output_tokens=data.get("meta", {}).get("billed_units", {}).get("output_tokens"),
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
        url = f"{self.api_base}/chat"
        headers = self._build_headers()
        body = self._build_chat_body(data)
        body["stream"] = True

        async with self.http_client.stream("POST", url, headers=headers, json=body) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip().startswith("data: "):
                    continue

                data_str = line[6:].strip()
                try:
                    data = json.loads(data_str)

                    # Check if stream is finished
                    if data.get("is_finished") or data.get("finish_reason"):
                        break

                    # Yield text content
                    if "text" in data:
                        yield data["text"]

                except json.JSONDecodeError:
                    continue

    async def embeddings(self, data: EmbeddingsData) -> list[list[float]]:
        """Make embedding request.

        Args:
            data: Embedding data

        Returns:
            List of embedding vectors
        """
        url = f"{self.api_base}/embed"
        headers = self._build_headers()
        body = {
            "texts": data.texts,
            "model": self.model.real_name(),
            "input_type": "search_query" if data.query else "search_document",
        }

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        result = response.json()
        return result.get("embeddings", [])

    async def rerank(self, data: RerankData) -> list:
        """Perform reranking.

        Args:
            data: Rerank data with query and documents

        Returns:
            Reranking results
        """
        url = f"{self.api_base}/rerank"
        headers = self._build_headers()
        body = {
            "model": self.model.real_name(),
            "query": data.query,
            "documents": data.documents,
            "top_n": data.top_n,
        }

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        result = response.json()
        return result.get("results", [])


__all__ = ["CohereClient"]
