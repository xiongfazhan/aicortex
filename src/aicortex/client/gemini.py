"""Gemini API client.

Corresponds to src/client/gemini.rs in the Rust implementation.
"""

import httpx
import json
from typing import AsyncIterator, Optional

from .mod import Client, ChatCompletionsData, ChatCompletionsOutput, EmbeddingsData
from .model import Model


class GeminiClient(Client):
    """Gemini API client.

    Implements the Client interface for Google's Gemini API.
    """

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: dict, model: Model):
        """Initialize Gemini client.

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
        }

    def _build_chat_body(self, data: ChatCompletionsData) -> dict:
        """Build chat completion request body for Gemini.

        Args:
            data: Chat completion data

        Returns:
            Request body dictionary
        """
        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for msg in data.messages:
            if msg.role.is_system():
                # System message
                if isinstance(msg.content, str):
                    system_instruction = msg.content
            else:
                # User/Assistant messages
                role = "user" if msg.role.is_user() else "model"
                parts = []

                if isinstance(msg.content, str):
                    parts.append({"text": msg.content})
                elif isinstance(msg.content, list):
                    for part in msg.content:
                        if part.type == "text":
                            parts.append({"text": part.text})
                        elif part.type == "image_url":
                            # Handle image
                            url = part.image_url.url
                            if url.startswith("data:"):
                                # Base64 image
                                mime_type, base64_data = url.split(";", 1)[1].split(",", 1)
                                parts.append({
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": base64_data,
                                    }
                                })

                if parts:
                    contents.append({"role": role, "parts": parts})

        body = {
            "contents": contents,
        }

        if system_instruction:
            body["system_instruction"] = {"parts": [{"text": system_instruction}]}

        # Generation config
        gen_config = {}
        if data.temperature is not None:
            gen_config["temperature"] = data.temperature
        if data.top_p is not None:
            gen_config["topP"] = data.top_p

        if gen_config:
            body["generationConfig"] = gen_config

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
        model_name = self.model.real_name()
        url = f"{self.api_base}/models/{model_name}:generateContent?key={self.api_key}"
        headers = self._build_headers()
        body = self._build_chat_body(data)

        response = await self.http_client.post(url, headers=headers, json=body)
        response.raise_for_status()

        return self._parse_chat_response(response.json())

    def _parse_chat_response(self, data: dict) -> ChatCompletionsOutput:
        """Parse Gemini chat completion response.

        Args:
            data: Response JSON data

        Returns:
            Parsed output
        """
        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                text += part.get("text", "")

        usage = data.get("usageMetadata", {})

        return ChatCompletionsOutput(
            text=text,
            tool_calls=[],
            id=data.get("id"),
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
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
        model_name = self.model.real_name()
        url = f"{self.api_base}/models/{model_name}:streamGenerateContent?key={self.api_key}"
        headers = self._build_headers()
        body = self._build_chat_body(data)

        async with self.http_client.stream("POST", url, headers=headers, json=body) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield text
                except json.JSONDecodeError:
                    continue

    async def embeddings(self, data: EmbeddingsData) -> list[list[float]]:
        """Make embedding request.

        Args:
            data: Embedding data

        Returns:
            List of embedding vectors
        """
        model_name = self.model.real_name()
        url = f"{self.api_base}/models/{model_name}:embedContent?key={self.api_key}"
        headers = self._build_headers()

        results = []
        for text in data.texts:
            body = {
                "content": {
                    "parts": [{"text": text}]
                }
            }

            response = await self.http_client.post(url, headers=headers, json=body)
            response.raise_for_status()

            result = response.json()
            embedding = result.get("embedding", {}).get("values", [])
            results.append(embedding)

        return results


__all__ = ["GeminiClient"]
