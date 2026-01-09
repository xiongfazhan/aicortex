"""Client module core.

Defines the Client interface and common functionality.
Corresponds to src/client/mod.rs and src/client/common.rs in the Rust implementation.
"""

import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Union
import asyncio
from ..utils import estimate_token_length, strip_think_tag
from .message import Message, MessageContent, MessageContentPart, MessageContentToolCalls
from .model import Model, ModelType

# Constants
PER_MESSAGES_TOKENS = 5
BASIS_TOKENS = 2

# OpenAI-compatible providers
OPENAI_COMPATIBLE_PROVIDERS = {
    "ai21": "https://api.ai21.com/studio/v1",
    "cloudflare": "https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/v1",
    "deepinfra": "https://api.deepinfra.com/v1/openai",
    "deepseek": "https://api.deepseek.com",
    "ernie": "https://qianfan.baidubce.com/v2",
    "github": "https://models.inference.ai.azure.com",
    "groq": "https://api.groq.com/openai/v1",
    "hunyuan": "https://api.hunyuan.cloud.tencent.com/v1",
    "minimax": "https://api.minimax.chat/v1",
    "mistral": "https://api.mistral.ai/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "perplexity": "https://api.perplexity.ai",
    "qianwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "xai": "https://api.x.ai/v1",
    "zhipuai": "https://open.bigmodel.cn/api/paas/v4",
    # RAG-dedicated
    "jina": "https://api.jina.ai/v1",
    "voyageai": "https://api.voyageai.com/v1",
}


@dataclass
class ExtraConfig:
    """Extra client configuration."""

    proxy: Optional[str] = None
    connect_timeout: Optional[int] = None


@dataclass
class ChatCompletionsData:
    """Data for chat completion requests."""

    messages: list[Message]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    functions: Optional[list[dict]] = None
    stream: bool = False


@dataclass
class ChatCompletionsOutput:
    """Output from chat completion requests."""

    text: str
    tool_calls: list[Any] = field(default_factory=list)
    id: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    @classmethod
    def new(cls, text: str) -> "ChatCompletionsOutput":
        """Create new output with just text."""
        return cls(text=text)


@dataclass
class EmbeddingsData:
    """Data for embedding requests."""

    texts: list[str]
    query: bool = False
    model: Optional[str] = None
    input_type: Optional[str] = None  # For NIM: 'query' or 'passage'


@dataclass
class RerankData:
    """Data for reranking requests."""

    query: str
    documents: list[str]
    top_n: int = 5
    model: Optional[str] = None


class Client(ABC):
    """Base class for LLM clients.

    All client implementations must inherit from this class and implement
    the abstract methods for making API calls.
    """

    def __init__(
        self,
        config: dict[str, Any],
        model: Model,
        extra_config: Optional[ExtraConfig] = None,
    ):
        self.config = config
        self.model = model
        self.extra_config = extra_config or ExtraConfig()
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            timeout = httpx.Timeout(self.extra_config.connect_timeout or 10.0, connect=10.0)
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            self._http_client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
            )

            # Set proxy if configured
            if self.extra_config.proxy:
                self._http_client = httpx.AsyncClient(
                    timeout=timeout,
                    limits=limits,
                    proxy=self.extra_config.proxy,
                    follow_redirects=True,
                )

        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    @abstractmethod
    async def chat_completions(
        self, data: ChatCompletionsData
    ) -> ChatCompletionsOutput:
        """Make a non-streaming chat completion request.

        Args:
            data: The chat completion request data

        Returns:
            The chat completion response

        Raises:
            Exception: If the API call fails
        """
        pass

    @abstractmethod
    async def chat_completions_streaming(
        self, data: ChatCompletionsData
    ) -> "AsyncStreamHandler":
        """Make a streaming chat completion request.

        Args:
            data: The chat completion request data

        Returns:
            An async iterator that yields response chunks

        Raises:
            Exception: If the API call fails
        """
        pass

    async def embeddings(self, data: EmbeddingsData) -> list[list[float]]:
        """Make an embedding request.

        Args:
            data: The embedding request data

        Returns:
            List of embedding vectors

        Raises:
            NotImplementedError: If the client doesn't support embeddings
        """
        raise NotImplementedError("The client doesn't support embeddings API")

    async def rerank(
        self, data: RerankData
    ) -> list["RerankResult"]:
        """Make a reranking request.

        Args:
            data: The reranking request data

        Returns:
            List of reranked results with scores

        Raises:
            NotImplementedError: If the client doesn't support reranking
        """
        raise NotImplementedError("The client doesn't support rerank API")


class AsyncStreamHandler(ABC):
    """Handler for streaming responses.

    Provides methods to receive text chunks and manage the streaming state.
    """

    @abstractmethod
    async def text(self, chunk: str) -> None:
        """Receive a text chunk from the stream."""
        pass

    @abstractmethod
    async def done(self) -> None:
        """Signal that streaming is complete."""
        pass

    @abstractmethod
    def abort_signal(self) -> Any:
        """Get the abort signal for this stream."""
        pass


def estimate_tokens(messages: list[Message], model: Model) -> int:
    """Estimate token count for a list of messages.

    Args:
        messages: List of messages to count tokens for
        model: Model to use for estimation

    Returns:
        Estimated token count
    """
    if not messages:
        return 0

    messages_len = len(messages)
    message_tokens = 0

    for i, msg in enumerate(messages):
        match msg.content:
            case str(text):
                # Strip think tags from assistant messages (except last)
                if msg.role.value == "assistant" and i != messages_len - 1:
                    text = strip_think_tag(text)
                message_tokens += estimate_token_length(text)
            case list(parts):
                for part in parts:
                    if part.type == "text" and part.text:
                        message_tokens += estimate_token_length(part.text)
            case MessageContentToolCalls(tool_results, text, _):
                message_tokens += estimate_token_length(text)
                for result in tool_results:
                    import json

                    json_str = json.dumps(
                        {"name": result.call.name, "arguments": result.call.arguments}
                    )
                    message_tokens += estimate_token_length(json_str)

    # Add per-message overhead
    if messages[messages_len - 1].role.value == "user":
        return messages_len * PER_MESSAGES_TOKENS + message_tokens
    else:
        return (messages_len - 1) * PER_MESSAGES_TOKENS + message_tokens


def guard_max_tokens(messages: list[Message], model: Model) -> None:
    """Check that messages don't exceed max input tokens.

    Args:
        messages: List of messages to check
        model: Model with max_input_tokens limit

    Raises:
        ValueError: If tokens exceed limit
    """
    total_tokens = estimate_tokens(messages, model) + BASIS_TOKENS
    max_tokens = model.max_input_tokens()
    if max_tokens and total_tokens >= max_tokens:
        raise ValueError(f"Exceed max_input_tokens limit ({total_tokens} >= {max_tokens})")


__all__ = [
    "Client",
    "AsyncStreamHandler",
    "ExtraConfig",
    "ChatCompletionsData",
    "ChatCompletionsOutput",
    "EmbeddingsData",
    "RerankData",
    "OPENAI_COMPATIBLE_PROVIDERS",
    "estimate_tokens",
    "guard_max_tokens",
]
