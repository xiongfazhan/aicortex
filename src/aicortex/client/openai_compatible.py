"""OpenAI-compatible API client.

Corresponds to src/client/openai_compatible.rs in the Rust implementation.

Supports various providers that offer OpenAI-compatible APIs.
"""

import json
from typing import AsyncIterator

from .mod import Client, ChatCompletionsData, ChatCompletionsOutput, EmbeddingsData, RerankData
from .openai import OpenAIClient
from .model import Model


# OpenAI-compatible providers and their default API bases
OPENAI_COMPATIBLE_PROVIDERS = {
    "openai": "https://api.openai.com/v1",
    "azure": "",  # Azure has custom base format
    "deepseek": "https://api.deepseek.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "perplexity": "https://api.perplexity.ai",
    "together": "https://api.together.xyz/v1",
    "mistral": "https://api.mistral.ai/v1",
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "cohere": "https://api.cohere.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "voyageai": "https://api.voyageai.com/v1",
    "ernie": "",  # Custom handling
    "nim": "https://integrate.api.nvidia.com/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
}


class OpenAICompatibleClient(OpenAIClient):
    """OpenAI-compatible API client.

    Extends OpenAIClient to work with various OpenAI-compatible providers.
    """

    def __init__(self, config: dict, model: Model):
        """Initialize OpenAI-compatible client.

        Args:
            config: Client configuration
            model: Model to use
        """
        # Set default api_base if not provided
        if not config.get("api_base"):
            provider = model.client_name
            if provider in OPENAI_COMPATIBLE_PROVIDERS:
                api_base = OPENAI_COMPATIBLE_PROVIDERS[provider]
                if api_base:
                    config["api_base"] = api_base

        super().__init__(config, model)
        self.client_name = model.client_name

    def _build_chat_body(self, data: ChatCompletionsData) -> dict:
        """Build chat completion request body.

        Args:
            data: Chat completion data

        Returns:
            Request body dictionary
        """
        body = super()._build_chat_body(data)

        # Provider-specific adjustments
        if self.client_name.startswith("voyageai"):
            # VoyageAI uses top_k instead of top_n
            pass  # Would need to handle in request

        return body

    async def rerank(self, data: RerankData) -> list:
        """Perform reranking.

        Args:
            data: Rerank data with query and documents

        Returns:
            Reranking results
        """
        api_base = self.api_base

        # Determine endpoint based on provider
        if self.client_name in ("nim", "nvidia"):
            # NIM uses special endpoint: ai.api.nvidia.com/v1/retrieval/{model}/reranking
            model_name = data.model or self.model.real_name()
            # Replace . with _ in model name for URL
            model_url_name = model_name.replace(".", "_").replace("/", "/")
            endpoint = f"https://ai.api.nvidia.com/v1/retrieval/{model_url_name}/reranking"
        elif self.client_name.startswith("ernie"):
            endpoint = f"{api_base}/rerankers"
        else:
            endpoint = f"{api_base}/rerank"

        body = self._build_rerank_body(data)

        headers = self._build_headers()
        response = await self.http_client.post(endpoint, headers=headers, json=body)
        response.raise_for_status()

        result = response.json()

        # Handle NIM response format
        if "rankings" in result:
            # NIM returns {rankings: [{index, logit}, ...]}
            return [
                {"index": r["index"], "relevance_score": r.get("logit", 0)}
                for r in result["rankings"]
            ]

        # Some providers return results in data.results
        if "results" not in result and "data" in result:
            result["results"] = result["data"]

        return result.get("results", [])

    def _build_rerank_body(self, data: RerankData) -> dict:
        """Build rerank request body.

        Args:
            data: Rerank data

        Returns:
            Request body dictionary
        """
        model_name = data.model or self.model.real_name()

        # NIM uses different body format
        if self.client_name in ("nim", "nvidia"):
            return {
                "model": model_name,
                "query": {"text": data.query},
                "passages": [{"text": doc} for doc in data.documents],
            }

        body = {
            "model": model_name,
            "query": data.query,
            "documents": data.documents,
        }

        # Use top_k or top_n based on provider
        if self.client_name.startswith("voyageai"):
            body["top_k"] = data.top_n
        else:
            body["top_n"] = data.top_n

        return body


__all__ = ["OpenAICompatibleClient", "OPENAI_COMPATIBLE_PROVIDERS"]
