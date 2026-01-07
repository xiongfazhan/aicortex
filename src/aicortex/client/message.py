"""Message definitions.

Corresponds to src/client/message.rs in the Rust implementation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Union


class MessageRole(Enum):
    """Message role enumeration."""

    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    TOOL = "tool"

    def is_system(self) -> bool:
        """Check if this is a system message."""
        return self == MessageRole.SYSTEM

    def is_user(self) -> bool:
        """Check if this is a user message."""
        return self == MessageRole.USER

    def is_assistant(self) -> bool:
        """Check if this is an assistant message."""
        return self == MessageRole.ASSISTANT


@dataclass
class ImageUrl:
    """Image URL for vision models."""

    url: str


@dataclass
class MessageContentPart:
    """A part of message content (for multi-modal messages)."""

    type: str  # "text" or "image_url"
    text: str | None = None
    image_url: ImageUrl | None = None


@dataclass
class ToolCall:
    """A tool call (function call) made by the model."""

    name: str
    arguments: dict  # JSON object
    id: str | None = None


@dataclass
class ToolResult:
    """Result of executing a tool call."""

    call: ToolCall
    output: dict  # JSON object


@dataclass
class MessageContentToolCalls:
    """Tool calls content type."""

    tool_results: list[ToolResult]
    text: str = ""
    sequence: bool = False

    @classmethod
    def new(cls, tool_results: list[ToolResult], text: str) -> "MessageContentToolCalls":
        """Create new tool calls content."""
        return cls(tool_results=tool_results, text=text, sequence=False)

    def merge(self, tool_results: list[ToolResult], text: str) -> None:
        """Merge additional tool results."""
        self.tool_results.extend(tool_results)
        self.text = ""
        self.sequence = True


MessageContent = Union[str, list[MessageContentPart], MessageContentToolCalls]


@dataclass
class Message:
    """A chat message.

    Can represent a system, user, assistant, or tool message.
    Content can be text, multi-modal (text + images), or tool calls.
    """

    role: MessageRole
    content: MessageContent

    @classmethod
    def new(cls, role: MessageRole, content: MessageContent) -> "Message":
        """Create a new message."""
        return cls(role=role, content=content)

    def merge_system(self, system: MessageContent) -> None:
        """Merge system message content into this message."""
        if isinstance(self.content, str):
            if isinstance(system, str):
                self.content = [
                    MessageContentPart(type="text", text=system),
                    MessageContentPart(type="text", text=self.content),
                ]
            elif isinstance(system, list):
                self.content = system + [
                    MessageContentPart(type="text", text=self.content)
                ]
        elif isinstance(self.content, list):
            if isinstance(system, str):
                self.content.insert(
                    0, MessageContentPart(type="text", text=system)
                )
            elif isinstance(system, list):
                self.content = system + self.content
        # ToolCalls: no merge needed

    def to_dict(self) -> dict:
        """Convert message to API format.

        Returns:
            Dictionary suitable for JSON serialization in API requests
        """
        if isinstance(self.content, str):
            return {"role": self.role.value, "content": self.content}
        elif isinstance(self.content, list):
            content_list = []
            for part in self.content:
                if part.type == "text":
                    content_list.append({"type": "text", "text": part.text})
                elif part.type == "image_url":
                    content_list.append(
                        {"type": "image_url", "image_url": {"url": part.image_url.url}}
                    )
            return {"role": self.role.value, "content": content_list}
        elif isinstance(self.content, MessageContentToolCalls):
            # Build tool calls format
            tool_calls = []
            for result in self.content.tool_results:
                tool_calls.append(
                    {
                        "id": result.call.id or "",
                        "type": "function",
                        "function": {
                            "name": result.call.name,
                            "arguments": __import__("json").dumps(
                                result.call.arguments
                            ),
                        },
                    }
                )
            return {"role": self.role.value, "content": self.content.text, "tool_calls": tool_calls}

    def to_text(self) -> str:
        """Extract text content from message.

        Returns:
            All text parts joined together
        """
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            parts = []
            for part in self.content:
                if part.text:
                    parts.append(part.text)
            return "\n\n".join(parts)
        elif isinstance(self.content, MessageContentToolCalls):
            return self.content.text
        return ""


def patch_messages(messages: list[Message], model) -> None:
    """Patch messages to handle system prompt prefixes and message format.

    Args:
        messages: List of messages to patch (modified in place)
        model: Model instance to check for system_prompt_prefix and no_system_message
    """
    if not messages:
        return

    # Add system prompt prefix if needed
    if hasattr(model, "system_prompt_prefix"):
        prefix = model.system_prompt_prefix()
        if prefix:
            if messages[0].role == MessageRole.SYSTEM:
                messages[0].merge_system(prefix)
            else:
                messages.insert(
                    0,
                    Message.new(MessageRole.SYSTEM, prefix),
                )

    # Handle models that don't support system messages
    if hasattr(model, "no_system_message") and model.no_system_message():
        if messages[0].role == MessageRole.SYSTEM:
            system_message = messages.pop(0)
            if messages:
                messages[0].merge_system(system_message.content)


def extract_system_message(messages: list[Message]) -> str | None:
    """Extract and remove the system message from the list.

    Args:
        messages: List of messages (modified in place)

    Returns:
        System message text, or None if no system message
    """
    if messages and messages[0].role == MessageRole.SYSTEM:
        system_message = messages.pop(0)
        return system_message.to_text()
    return None


__all__ = [
    "MessageRole",
    "Message",
    "MessageContent",
    "MessageContentPart",
    "MessageContentToolCalls",
    "ImageUrl",
    "ToolCall",
    "ToolResult",
    "patch_messages",
    "extract_system_message",
]
