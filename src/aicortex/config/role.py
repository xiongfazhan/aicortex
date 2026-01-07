"""Role management.

Corresponds to src/config/role.rs in the Rust implementation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol
import re
import yaml

from ..client import Model, Message, MessageRole, MessageContent
from ..utils.variables import interpolate_variables

# Metadata regex for parsing role files
RE_METADATA = re.compile(r"(?s)-{3,}\s*(.*?)\s*-{3,}\s*(.*)")

# Input placeholder
INPUT_PLACEHOLDER = "__INPUT__"

# Built-in role names
SHELL_ROLE = "%shell%"
EXPLAIN_SHELL_ROLE = "%explain-shell%"
CODE_ROLE = "%code%"
CREATE_TITLE_ROLE = "%create-title%"


class RoleLike(Protocol):
    """Protocol for types that have role-like properties."""

    def to_role(self) -> "Role": ...
    def model(self) -> Model: ...
    def temperature(self) -> Optional[float]: ...
    def top_p(self) -> Optional[float]: ...
    def use_tools(self) -> Optional[str]: ...
    def set_model(self, model: Model) -> None: ...
    def set_temperature(self, value: Optional[float]) -> None: ...
    def set_top_p(self, value: Optional[float]) -> None: ...
    def set_use_tools(self, value: Optional[str]) -> None: ...


@dataclass
class Role:
    """A role definition for LLM prompts.

    Roles define how the AI should behave, including system prompts,
    model settings, and tool configurations.
    """

    name: str
    prompt: str = ""
    model_id: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    use_tools: Optional[str] = None
    model: Model = field(default_factory=lambda: Model.new("", ""))

    @classmethod
    def new(cls, name: str, content: str) -> "Role":
        """Create a new role from markdown content.

        Args:
            name: Role name
            content: Markdown content, possibly with YAML metadata

        Returns:
            A new Role instance
        """
        metadata = ""
        prompt = content.strip()

        # Try to extract metadata
        match = RE_METADATA.match(content)
        if match:
            metadata = match.group(1).strip()
            prompt = match.group(2).strip()

        # Interpolate variables in prompt
        prompt = interpolate_variables(prompt)

        role = cls(name=name, prompt=prompt)

        # Parse metadata if present
        if metadata:
            try:
                data = yaml.safe_load(metadata)
                if isinstance(data, dict):
                    role.model_id = data.get("model")
                    role.temperature = data.get("temperature")
                    role.top_p = data.get("top_p")
                    role.use_tools = data.get("use_tools")
            except yaml.YAMLError:
                pass

        return role

    @classmethod
    def builtin(cls, name: str) -> "Role":
        """Load a built-in role from assets.

        Args:
            name: Role name (without .md extension)

        Returns:
            Role instance

        Raises:
            FileNotFoundError: If role file doesn't exist
        """
        import importlib.resources

        try:
            # Try to load from package resources
            content = (importlib.resources.files("assets.roles") / f"{name}.md").read_text()
        except (FileNotFoundError, AttributeError):
            # Fallback to directory-relative path
            role_path = Path(__file__).parent.parent.parent / "assets" / "roles" / f"{name}.md"
            if not role_path.exists():
                raise FileNotFoundError(f"Unknown role `{name}`")
            content = role_path.read_text()

        return cls.new(name, content)

    @classmethod
    def list_builtin_role_names(cls) -> list[str]:
        """List all built-in role names.

        Returns:
            List of role names (without .md extension)
        """
        import importlib.resources

        try:
            return [
                f.stem.split(".")[0]
                for f in (importlib.resources.files("assets.roles")).iterdir()
                if f.suffix == ".md"
            ]
        except (FileNotFoundError, AttributeError):
            role_dir = Path(__file__).parent.parent.parent / "assets" / "roles"
            if role_dir.exists():
                return [f.stem for f in role_dir.glob("*.md")]
            return []

    @classmethod
    def list_builtin_roles(cls) -> list["Role"]:
        """List all built-in roles.

        Returns:
            List of Role instances
        """
        names = []
        try:
            import importlib.resources
            names = [
                f.stem.split(".")[0]
                for f in (importlib.resources.files("assets.roles")).iterdir()
                if f.suffix == ".md"
            ]
        except (FileNotFoundError, AttributeError):
            role_dir = Path(__file__).parent.parent.parent / "assets" / "roles"
            if role_dir.exists():
                names = [f.stem for f in role_dir.glob("*.md")]

        return [cls.builtin(name) for name in names]

    def has_args(self) -> bool:
        """Check if role name contains argument placeholder.

        Returns:
            True if name contains '#'
        """
        return "#" in self.name

    def export(self) -> str:
        """Export role to markdown format.

        Returns:
            Markdown string with metadata and prompt
        """
        metadata_parts = []
        if self.model_id:
            metadata_parts.append(f"model: {self.model_id}")
        if self.temperature:
            metadata_parts.append(f"temperature: {self.temperature}")
        if self.top_p:
            metadata_parts.append(f"top_p: {self.top_p}")
        if self.use_tools:
            metadata_parts.append(f"use_tools: {self.use_tools}")

        if metadata_parts:
            if self.prompt:
                return f"---\n{chr(10).join(metadata_parts)}\n---\n\n{self.prompt}\n"
            else:
                return f"---\n{chr(10).join(metadata_parts)}\n---\n"
        else:
            return f"{self.prompt}\n"

    def save(self, role_name: str, role_path: Path, is_repl: bool = False) -> None:
        """Save role to file.

        Args:
            role_name: Name to save the role as
            role_path: Path to save to
            is_repl: Whether to print confirmation message
        """
        role_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.export()
        role_path.write_text(content)

        if is_repl:
            print(f"✓ Saved role to '{role_path}'.")

        if role_name != self.name:
            self.name = role_name

    def sync(self, role_like: RoleLike) -> None:
        """Sync role properties from another RoleLike instance.

        Args:
            role_like: Object to sync from
        """
        self.batch_set(
            role_like.model(),
            role_like.temperature(),
            role_like.top_p(),
            role_like.use_tools(),
        )

    def batch_set(
        self,
        model: Model,
        temperature: Optional[float],
        top_p: Optional[float],
        use_tools: Optional[str],
    ) -> None:
        """Set multiple properties at once.

        Args:
            model: Model to set
            temperature: Temperature parameter
            top_p: Top-p parameter
            use_tools: Tools to use
        """
        self.set_model(model)
        if temperature is not None:
            self.set_temperature(temperature)
        if top_p is not None:
            self.set_top_p(top_p)
        if use_tools is not None:
            self.set_use_tools(use_tools)

    def is_derived(self) -> bool:
        """Check if role is derived (has no name).

        Returns:
            True if name is empty
        """
        return not self.name

    def is_empty_prompt(self) -> bool:
        """Check if prompt is empty.

        Returns:
            True if prompt is empty
        """
        return not self.prompt

    def is_embedded_prompt(self) -> bool:
        """Check if prompt contains input placeholder.

        Returns:
            True if prompt contains INPUT_PLACEHOLDER
        """
        return INPUT_PLACEHOLDER in self.prompt

    def echo_messages(self, input_text: str) -> str:
        """Build echo text for input.

        Args:
            input_text: User input text

        Returns:
            Formatted text showing what will be sent
        """
        if self.is_empty_prompt():
            return input_text
        elif self.is_embedded_prompt():
            return self.prompt.replace(INPUT_PLACEHOLDER, input_text)
        else:
            return f"{self.prompt}\n\n{input_text}"

    # RoleLike protocol implementation
    def to_role(self) -> "Role":
        """Return self as a Role."""
        return Role(
            name=self.name,
            prompt=self.prompt,
            model_id=self.model_id,
            temperature=self.temperature,
            top_p=self.top_p,
            use_tools=self.use_tools,
            model=self.model,
        )

    def model(self) -> Model:
        """Get the model."""
        return self.model

    def set_model(self, model: Model) -> None:
        """Set the model."""
        if self.model.id():
            self.model_id = model.id()
        self.model = model

    def set_temperature(self, value: Optional[float]) -> None:
        """Set the temperature."""
        self.temperature = value

    def set_top_p(self, value: Optional[float]) -> None:
        """Set top_p."""
        self.top_p = value

    def set_use_tools(self, value: Optional[str]) -> None:
        """Set use_tools."""
        self.use_tools = value


def parse_structure_prompt(prompt: str) -> tuple[str, list[tuple[str, str]]]:
    """Parse a structured prompt with INPUT/OUTPUT markers.

    Args:
        prompt: Prompt text possibly containing ### INPUT: and ### OUTPUT: markers

    Returns:
        Tuple of (system_prompt, list of (input, output) pairs)
    """
    text = prompt
    search_input = True
    system = None
    parts = []

    while True:
        search = "### INPUT:" if search_input else "### OUTPUT:"
        idx = text.find(search)
        if idx >= 0:
            if system is None:
                system = text[:idx]
            else:
                parts.append(text[:idx])
            search_input = not search_input
            text = text[idx + len(search) :]
        else:
            if text:
                if system is None:
                    system = text
                else:
                    parts.append(text)
            break

    parts_len = len(parts)
    if parts_len > 0 and parts_len % 2 == 0:
        cases = [
            (parts[i].strip(), parts[i + 1].strip())
            for i in range(0, parts_len, 2)
        ]
        system_text = system.strip() if system else ""
        return (system_text, cases)

    return (prompt, [])


__all__ = [
    "Role",
    "RoleLike",
    "SHELL_ROLE",
    "EXPLAIN_SHELL_ROLE",
    "CODE_ROLE",
    "CREATE_TITLE_ROLE",
    "INPUT_PLACEHOLDER",
    "parse_structure_prompt",
]
