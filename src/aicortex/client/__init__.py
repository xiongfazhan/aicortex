"""Client module.

Corresponds to src/client/ in the Rust implementation.
"""

from .mod import (
    Client,
    AsyncStreamHandler,
    ExtraConfig,
    ChatCompletionsData,
    ChatCompletionsOutput,
    EmbeddingsData,
    RerankData,
    estimate_tokens,
    guard_max_tokens,
)
from .message import (
    MessageRole,
    Message,
    MessageContent,
    MessageContentPart,
    ImageUrl,
    MessageContentToolCalls,
    ToolCall,
    ToolResult,
    patch_messages,
    extract_system_message,
)
from .model import (
    ModelType,
    ModelData,
    Model,
    ProviderModels,
    RerankResult,
)
from .stream import (
    SseEvent,
    SseHandler,
    parse_openai_sse,
    iter_sse_lines,
    openai_chat_completions_streaming,
)
from .openai import OpenAIClient
from .claude import ClaudeClient
from .openai_compatible import OpenAICompatibleClient, OPENAI_COMPATIBLE_PROVIDERS
from .gemini import GeminiClient
from .cohere import CohereClient
from .azure_openai import AzureOpenAIClient

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
    "MessageRole",
    "Message",
    "MessageContent",
    "MessageContentPart",
    "ImageUrl",
    "MessageContentToolCalls",
    "ToolCall",
    "ToolResult",
    "patch_messages",
    "extract_system_message",
    "ModelType",
    "ModelData",
    "Model",
    "ProviderModels",
    "RerankResult",
    "SseEvent",
    "SseHandler",
    "parse_openai_sse",
    "iter_sse_lines",
    "openai_chat_completions_streaming",
    "OpenAIClient",
    "ClaudeClient",
    "OpenAICompatibleClient",
    "GeminiClient",
    "CohereClient",
    "AzureOpenAIClient",
]
