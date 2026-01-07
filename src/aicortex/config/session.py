"""Session management.

Corresponds to src/config/session.rs in the Rust implementation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import re
import yaml

from ..client import Model, Message, MessageRole, MessageContent
from .role import Role, RoleLike

# Constants
TEMP_SESSION_NAME = "temp"
RE_AUTONAME_PREFIX = re.compile(r"\d{8}T\d{6}-")


@dataclass
class AutoName:
    """Auto-generated session name."""

    naming: bool = False
    chat_history: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def new(cls, name: str) -> "AutoName":
        """Create new AutoName with a name."""
        return cls(name=name)

    @classmethod
    def new_from_chat_history(cls, chat_history: str) -> "AutoName":
        """Create AutoName from chat history."""
        return cls(chat_history=chat_history)

    def need(self) -> bool:
        """Check if autonaming is needed."""
        return not self.naming and self.chat_history is not None and self.name is None


@dataclass
class Session:
    """A chat session with message history.

    Sessions maintain conversation context across multiple interactions.
    """

    model_id: str
    name: str = TEMP_SESSION_NAME
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    use_tools: Optional[str] = None
    save_session: Optional[bool] = None
    compress_threshold: Optional[int] = None

    role_name: Optional[str] = None
    agent_variables: dict = field(default_factory=dict)
    agent_instructions: str = ""

    messages: list[Message] = field(default_factory=list)
    compressed_messages: list[Message] = field(default_factory=list)
    data_urls: dict[str, str] = field(default_factory=dict)

    # Non-serialized fields
    model: Model = field(default_factory=lambda: Model.new("", ""))
    role_prompt: str = ""
    path: Optional[str] = None
    dirty: bool = False
    save_session_this_time: bool = False
    compressing: bool = False
    autoname: Optional[AutoName] = None
    tokens: int = 0

    @classmethod
    def new(cls, config, name: str) -> "Session":
        """Create a new session.

        Args:
            config: Global configuration
            name: Session name

        Returns:
            New Session instance
        """
        role = getattr(config, "extract_role", lambda: None)()
        session = cls(name=name, save_session=getattr(config, "save_session", None))
        session.set_role(role)
        session.dirty = False
        return session

    @classmethod
    def load(cls, config, name: str, path: Path) -> "Session":
        """Load session from file.

        Args:
            config: Global configuration
            name: Session name
            path: Path to session file

        Returns:
            Loaded Session instance

        Raises:
            FileNotFoundError: If session file doesn't exist
            ValueError: If session file is invalid
        """
        content = path.read_text()
        data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid session {name}")

        # Create session from data
        session = cls(**{
            k: v
            for k, v in data.items()
            if k
            in [
                "model_id",
                "name",
                "temperature",
                "top_p",
                "use_tools",
                "save_session",
                "compress_threshold",
                "role_name",
                "agent_variables",
                "agent_instructions",
                "messages",
                "compressed_messages",
                "data_urls",
            ]
        })

        # Resolve model
        # session.model = Model.retrieve_model(config, session.model_id, ModelType.CHAT)

        # Handle autoname sessions
        if name.startswith("_/"):
            session.name = TEMP_SESSION_NAME
            session.path = None
            autoname = name[2:]
            if RE_AUTONAME_PREFIX.match(autoname):
                session.autoname = AutoName.new(autoname[16:])
        else:
            session.name = name
            session.path = str(path)

        # Load role prompt if specified
        if session.role_name:
            try:
                role = config.retrieve_role(session.role_name)
                session.role_prompt = role.prompt
            except (FileNotFoundError, AttributeError):
                pass

        session.update_tokens()
        return session

    def is_empty(self) -> bool:
        """Check if session has no messages.

        Returns:
            True if no messages in session
        """
        return not self.messages and not self.compressed_messages

    def update_tokens(self) -> None:
        """Update token count for current messages."""
        # Estimate tokens (simplified)
        self.tokens = sum(len(str(msg.content)) // 4 for msg in self.messages)

    def has_user_messages(self) -> bool:
        """Check if session has user messages.

        Returns:
            True if there are user messages
        """
        return any(msg.role == MessageRole.USER for msg in self.messages)

    def user_messages_len(self) -> int:
        """Count user messages.

        Returns:
            Number of user messages
        """
        return sum(1 for msg in self.messages if msg.role == MessageRole.USER)

    def tokens_usage(self) -> tuple[int, float]:
        """Get token usage statistics.

        Returns:
            Tuple of (tokens, percentage of max)
        """
        tokens = self.tokens
        max_tokens = self.model.max_input_tokens() or 0
        if max_tokens == 0:
            percent = 0.0
        else:
            percent = round((tokens / max_tokens) * 100, 2)
        return (tokens, percent)

    def set_role(self, role: Role) -> None:
        """Set role for session.

        Args:
            role: Role to use
        """
        self.model_id = role.model.id()
        self.temperature = role.temperature
        self.top_p = role.top_p
        self.use_tools = role.use_tools
        self.model = role.model
        self.role_name = role.name if role.name else None
        self.role_prompt = role.prompt
        self.dirty = True
        self.update_tokens()

    def clear_role(self) -> None:
        """Clear role from session."""
        self.role_name = None
        self.role_prompt = ""

    def set_save_session(self, value: Optional[bool]) -> None:
        """Set save_session flag.

        Args:
            value: Save session flag
        """
        if self.save_session != value:
            self.save_session = value
            self.dirty = True

    def set_save_session_this_time(self) -> None:
        """Mark session to be saved this time."""
        self.save_session_this_time = True

    def set_compress_threshold(self, value: Optional[int]) -> None:
        """Set compression threshold.

        Args:
            value: Token threshold for compression
        """
        if self.compress_threshold != value:
            self.compress_threshold = value
            self.dirty = True

    def need_compress(self, global_threshold: int) -> bool:
        """Check if session needs compression.

        Args:
            global_threshold: Global compression threshold

        Returns:
            True if compression needed
        """
        if self.compressing:
            return False
        threshold = self.compress_threshold or global_threshold
        if threshold < 1:
            return False
        return self.tokens > threshold

    def compress(self, prompt: str) -> None:
        """Compress session messages.

        Args:
            prompt: Summary prompt to use
        """
        # Add system message if present at start
        if self.messages and self.messages[0].role == MessageRole.SYSTEM:
            system_text = self.messages[0].content.to_text()
            if system_text:
                prompt = f"{system_text}\n\n{prompt}"

        # Move all messages to compressed
        self.compressed_messages.extend(self.messages)
        self.messages = [
            Message.new(MessageRole.SYSTEM, MessageContent.Text(prompt))
        ]
        self.dirty = True
        self.update_tokens()

    def need_autoname(self) -> bool:
        """Check if autonaming is needed.

        Returns:
            True if autonaming is needed
        """
        return self.autoname.need() if self.autoname else False

    def set_autoname(self, value: str) -> None:
        """Set auto-generated name.

        Args:
            value: Name to set
        """
        # Convert to alphanumeric with dashes
        name = "".join(c if c.isalnum() else "-" for c in value)
        self.autoname = AutoName.new(name)

    def exit_session(self, session_dir: Path, is_repl: bool = True) -> None:
        """Exit session, optionally saving.

        Args:
            session_dir: Directory to save sessions to
            is_repl: Whether running in REPL mode
        """
        save_session = self.save_session
        if self.save_session_this_time:
            save_session = True

        if self.dirty and save_session is not False:
            session_dir = Path(session_dir)
            session_name = self.name

            if save_session is None:
                if not is_repl:
                    return
                # Prompt to save (simplified - would use questionary in full impl)
                if not self._confirm_save():
                    return
                if session_name == TEMP_SESSION_NAME:
                    session_name = self._prompt_session_name()

            # Save session
            session_path = session_dir / f"{session_name}.yaml"
            self.save(session_name, session_path, is_repl)

    def _confirm_save(self) -> bool:
        """Ask user to confirm save (simplified)."""
        return True  # In full impl, would use questionary.confirm

    def _prompt_session_name(self) -> str:
        """Prompt user for session name (simplified)."""
        return "session"  # In full impl, would use questionary.text

    def save(self, session_name: str, session_path: Path, is_repl: bool) -> None:
        """Save session to file.

        Args:
            session_name: Name to save as
            session_path: Path to save to
            is_repl: Whether to print confirmation
        """
        session_path.parent.mkdir(parents=True, exist_ok=True)
        self.path = str(session_path)

        # Build data dict (exclude non-serializable fields)
        data = {
            "model": self.model_id,
            "messages": self.messages,
        }
        if self.temperature:
            data["temperature"] = self.temperature
        if self.top_p:
            data["top_p"] = self.top_p
        if self.use_tools:
            data["use_tools"] = self.use_tools
        if self.save_session:
            data["save_session"] = self.save_session
        if self.compress_threshold:
            data["compress_threshold"] = self.compress_threshold
        if self.role_name:
            data["role_name"] = self.role_name
        if self.agent_variables:
            data["agent_variables"] = self.agent_variables
        if self.agent_instructions:
            data["agent_instructions"] = self.agent_instructions
        if self.compressed_messages:
            data["compressed_messages"] = self.compressed_messages
        if self.data_urls:
            data["data_urls"] = self.data_urls

        content = yaml.dump(data, allow_unicode=True)
        session_path.write_text(content)

        if is_repl:
            print(f"✓ Saved the session to '{session_path}'.")

        if session_name != self.name:
            self.name = session_name

        self.dirty = False

    def guard_empty(self) -> None:
        """Guard that session is empty.

        Raises:
            ValueError: If session has messages
        """
        if not self.is_empty():
            raise ValueError(
                "Cannot perform this operation because the session has messages, "
                "please `.empty session` first."
            )

    def add_message(self, input_text: str, output: str) -> None:
        """Add a message exchange to the session.

        Args:
            input_text: User input
            output: Assistant response
        """
        # Simplified implementation
        if not self.messages:
            self.messages.append(Message.new(MessageRole.USER, input_text))
        self.messages.append(
            Message.new(MessageRole.ASSISTANT, MessageContent.Text(output))
        )
        self.dirty = True
        self.update_tokens()

    def clear_messages(self) -> None:
        """Clear all messages from session."""
        self.messages.clear()
        self.compressed_messages.clear()
        self.data_urls.clear()
        self.autoname = None
        self.dirty = True
        self.update_tokens()

    def build_messages(self, input_text: str) -> list[Message]:
        """Build message list for API call.

        Args:
            input_text: User input text

        Returns:
            List of messages to send
        """
        messages = list(self.messages)

        # Add role prompt if present
        if self.role_prompt and not messages:
            # Parse structured prompt
            system, cases = parse_structure_prompt(self.role_prompt)
            if system:
                messages.append(Message.new(MessageRole.SYSTEM, system))
            for inp, outp in cases:
                messages.append(Message.new(MessageRole.USER, inp))
                messages.append(Message.new(MessageRole.ASSISTANT, outp))

        # Add current input
        messages.append(Message.new(MessageRole.USER, input_text))

        return messages

    # RoleLike protocol implementation
    def to_role(self) -> Role:
        """Convert session to a Role."""
        role = Role.new(self.role_name or "", self.role_prompt)
        role.sync(self)
        return role


def parse_structure_prompt(prompt: str) -> tuple[str, list[tuple[str, str]]]:
    """Parse a structured prompt with INPUT/OUTPUT markers.

    This is duplicated from role.py for avoiding circular imports.
    """
    from .role import parse_structure_prompt
    return parse_structure_prompt(prompt)


__all__ = [
    "Session",
    "TEMP_SESSION_NAME",
    "AutoName",
]
