"""Input handling.

Corresponds to src/config/input.rs in the Rust implementation.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path

from ..client import Message, MessageContent, MessageContentPart, ImageUrl
from .role import Role


@dataclass
class Input:
    """User input for LLM requests.

    Handles various input sources including plain text, files,
    directories, URLs, and command outputs.
    """

    config: Any  # GlobalConfig
    text: str
    raw_text: str = ""
    files: list[str] = field(default_factory=list)
    medias: list[str] = field(default_factory=list)
    continue_output: Optional[str] = None
    regenerate: bool = False
    tool_calls: Optional[Any] = None

    def __post_init__(self):
        """Initialize derived fields."""
        self.raw_text = self.text

    @classmethod
    def from_str(cls, config, text: str) -> "Input":
        """Create input from plain text.

        Args:
            config: Global configuration
            text: Input text

        Returns:
            Input instance
        """
        return cls(config=config, text=text)

    @classmethod
    def from_files(cls, config, text: str, files: list[str]) -> "Input":
        """Create input from files.

        Args:
            config: Global configuration
            text: Input text
            files: List of file paths

        Returns:
            Input instance
        """
        return cls(config=config, text=text, files=files)

    def message_content(self) -> MessageContent:
        """Build message content from input.

        Returns:
            MessageContent for API request
        """
        if not self.files and not self.medias:
            return MessageContent.Text(self.text)

        parts = []
        if self.text:
            parts.append(MessageContentPart(type="text", text=self.text))

        # Add images
        for media_url in self.medias:
            parts.append(
                MessageContentPart(
                    type="image_url", image_url=ImageUrl(url=media_url)
                )
            )

        # Add file contents (simplified)
        for file_path in self.files:
            try:
                content = Path(file_path).read_text()
                parts.append(MessageContentPart(type="text", text=content))
            except Exception:
                parts.append(MessageContentPart(type="text", text=f"[File: {file_path}]"))

        return parts

    def role(self) -> Role:
        """Get the role to use for this input.

        Returns:
            Role instance
        """
        if hasattr(self.config, "role") and self.config.role:
            return self.config.role
        return Role.new("", "")


__all__ = ["Input"]
