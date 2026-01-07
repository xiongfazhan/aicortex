"""Model definitions and management.

Corresponds to src/client/model.rs in the Rust implementation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class ModelType(Enum):
    """Model type enumeration."""

    CHAT = "chat"
    EMBEDDING = "embedding"
    RERANKER = "reranker"

    def can_create_from_name(self) -> bool:
        """Check if this model type can be created from just a name."""
        return self in (ModelType.CHAT, ModelType.RERANKER)

    def api_name(self) -> str:
        """Get the API name for this model type."""
        match self:
            case ModelType.CHAT:
                return "chat_completions"
            case ModelType.EMBEDDING:
                return "embeddings"
            case ModelType.RERANKER:
                return "rerank"


@dataclass
class ModelData:
    """Model configuration data."""

    name: str
    model_type: str = "chat"
    real_name: Optional[str] = None
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_price: Optional[float] = None
    output_price: Optional[float] = None
    patch: Optional[dict] = None

    # Chat-only properties
    require_max_tokens: bool = False
    supports_vision: bool = False
    supports_function_calling: bool = False
    no_stream: bool = False
    no_system_message: bool = False
    system_prompt_prefix: Optional[str] = None

    # Embedding-only properties
    max_tokens_per_chunk: Optional[int] = None
    default_chunk_size: Optional[int] = None
    max_batch_size: Optional[int] = None

    @classmethod
    def new(cls, name: str) -> "ModelData":
        """Create new model data with default values."""
        return cls(name=name)


@dataclass
class Model:
    """Model instance.

    Represents a specific model from a specific client.
    """

    client_name: str
    data: ModelData

    @classmethod
    def new(cls, client_name: str, name: str) -> "Model":
        """Create a new model instance."""
        return cls(client_name=client_name, data=ModelData.new(name))

    @classmethod
    def from_config(cls, client_name: str, models: list[ModelData]) -> list["Model"]:
        """Create multiple models from config data."""
        return [
            cls(client_name=client_name, data=model_data) for model_data in models
        ]

    def id(self) -> str:
        """Get the full model ID (client:name)."""
        if not self.data.name:
            return self.client_name
        return f"{self.client_name}:{self.data.name}"

    def name(self) -> str:
        """Get the model name."""
        return self.data.name

    def real_name(self) -> str:
        """Get the real model name (for API calls)."""
        return self.data.real_name or self.data.name

    def model_type(self) -> ModelType:
        """Get the model type."""
        type_str = self.data.model_type.lower()
        if type_str.startswith("embed"):
            return ModelType.EMBEDDING
        elif type_str.startswith("rerank"):
            return ModelType.RERANKER
        else:
            return ModelType.CHAT

    def patch(self) -> Optional[dict]:
        """Get the request patch configuration."""
        return self.data.patch

    def max_input_tokens(self) -> Optional[int]:
        """Get max input tokens."""
        return self.data.max_input_tokens

    def max_output_tokens(self) -> Optional[int]:
        """Get max output tokens."""
        return self.data.max_output_tokens

    def no_stream(self) -> bool:
        """Check if streaming is not supported."""
        return self.data.no_stream

    def no_system_message(self) -> bool:
        """Check if system messages are not supported."""
        return self.data.no_system_message

    def system_prompt_prefix(self) -> Optional[str]:
        """Get the system prompt prefix."""
        return self.data.system_prompt_prefix

    def max_tokens_per_chunk(self) -> Optional[int]:
        """Get max tokens per chunk for embeddings."""
        return self.data.max_tokens_per_chunk

    def default_chunk_size(self) -> int:
        """Get default chunk size for embeddings."""
        return self.data.default_chunk_size or 1000

    def max_batch_size(self) -> Optional[int]:
        """Get max batch size for embeddings."""
        return self.data.max_batch_size

    def max_tokens_param(self) -> Optional[int]:
        """Get the max_tokens parameter value (if required)."""
        if self.data.require_max_tokens:
            return self.data.max_output_tokens
        return None

    def set_max_tokens(
        self, max_output_tokens: Optional[int], require_max_tokens: bool
    ) -> "Model":
        """Set max output tokens configuration."""
        if max_output_tokens is None or max_output_tokens == 0:
            self.data.max_output_tokens = None
        else:
            self.data.max_output_tokens = max_output_tokens
        self.data.require_max_tokens = require_max_tokens
        return self

    def description(self) -> str:
        """Get a description of the model for display.

        Returns formatted string showing capabilities and limits.
        """
        match self.model_type():
            case ModelType.CHAT:
                return self._chat_description()
            case ModelType.EMBEDDING:
                return self._embedding_description()
            case ModelType.RERANKER:
                return ""

    def _chat_description(self) -> str:
        """Generate description for chat models."""
        max_input = self._format_option(self.data.max_input_tokens)
        max_output = self._format_option(self.data.max_output_tokens)
        input_price = self._format_option(self.data.input_price)
        output_price = self._format_option(self.data.output_price)

        capabilities = []
        if self.data.supports_vision:
            capabilities.append("👁")
        if self.data.supports_function_calling:
            capabilities.append("⚒")

        caps_str = ("".join(capabilities) + " ").ljust(3)

        return f"{max_input:>8} / {max_output:>8}  |  {input_price:>6} / {output_price:>6}  {caps_str:>6}"

    def _embedding_description(self) -> str:
        """Generate description for embedding models."""
        max_tokens = self._format_option(self.data.max_tokens_per_chunk)
        max_batch = self._format_option(self.data.max_batch_size)
        price = self._format_option(self.data.input_price)
        return f"max-tokens:{max_tokens};max-batch:{max_batch};price:{price}"

    def _format_option(self, value: Optional[int | float]) -> str:
        """Format optional value for display."""
        if value is None:
            return "-"
        return str(value)


@dataclass
class ProviderModels:
    """A collection of models from a provider."""

    provider: str
    models: list[ModelData]


@dataclass
class RerankResult:
    """Result of reranking operation."""

    index: int
    relevance_score: float


__all__ = [
    "ModelType",
    "ModelData",
    "Model",
    "ProviderModels",
    "RerankResult",
]
