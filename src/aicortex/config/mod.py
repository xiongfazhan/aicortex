"""Configuration management core.

Corresponds to src/config/mod.rs in the Rust implementation.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any
import yaml

from ..client import Model
from .role import Role
from .session import Session


class WorkingMode(Enum):
    """Application working mode."""

    REPL = "repl"
    CMD = "cmd"
    SERVE = "serve"


@dataclass
class Config:
    """Global configuration for AIChat.

    Manages all application settings including model selection,
    behavior preferences, RAG settings, and runtime state.
    """

    # LLM Configuration
    model_id: str = "openai:gpt-3.5-turbo"
    temperature: Optional[float] = None
    top_p: Optional[float] = None

    # Behavior Configuration
    dry_run: bool = False
    stream: bool = True
    save: bool = False
    keybindings: str = "emacs"
    editor: Optional[str] = None
    wrap: Optional[str] = None
    wrap_code: bool = False

    # Function Calling
    function_calling: bool = True
    mapping_tools: dict[str, str] = field(default_factory=dict)
    use_tools: Optional[str] = None

    # Prelude Settings
    repl_prelude: Optional[str] = None
    cmd_prelude: Optional[str] = None
    agent_prelude: Optional[str] = None

    # Session Configuration
    save_session: Optional[bool] = None
    compress_threshold: int = 4000
    summarize_prompt: Optional[str] = None
    summary_prompt: Optional[str] = None

    # RAG Configuration
    rag_embedding_model: Optional[str] = None
    rag_reranker_model: Optional[str] = None
    rag_top_k: int = 5
    rag_chunk_size: Optional[int] = None
    rag_chunk_overlap: Optional[int] = None
    rag_template: Optional[str] = None
    document_loaders: dict[str, str] = field(default_factory=dict)

    # Appearance Configuration
    highlight: bool = True
    theme: Optional[str] = None
    left_prompt: Optional[str] = None
    right_prompt: Optional[str] = None

    # Other Settings
    serve_addr: Optional[str] = "127.0.0.1:8000"
    user_agent: Optional[str] = None
    save_shell_history: bool = True
    sync_models_url: Optional[str] = None

    # Client Configuration
    clients: list[dict] = field(default_factory=list)

    # Runtime State (not serialized)
    model: Optional[Model] = field(default=None, init=False, compare=False)
    role: Optional[Role] = field(default=None, init=False, compare=False)
    session: Optional[Session] = field(default=None, init=False, compare=False)
    working_mode: WorkingMode = field(default=WorkingMode.CMD, init=False, compare=False)

    _config_path: Optional[Path] = field(default=None, init=False, repr=False)

    @classmethod
    async def init(cls, working_mode: WorkingMode, info_flag: bool = False) -> "Config":
        """Initialize configuration.

        Args:
            working_mode: The mode the app will run in
            info_flag: Whether to show info and exit

        Returns:
            Initialized Config instance
        """
        self = cls()
        self.working_mode = working_mode

        # Load configuration file
        await self._load_config_file()

        # Initialize model
        if not self.model_id and self.clients:
            self.model_id = self._get_default_model()

        self.model = await self._resolve_model(self.model_id)

        return self

    async def _load_config_file(self) -> None:
        """Load configuration from YAML file."""
        config_path = self._get_config_path()
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    self._update_from_dict(data)

    def _get_config_path(self) -> Path:
        """Get the configuration file path.

        Returns:
            Path to config.yaml
        """
        if self._config_path:
            return self._config_path

        # Check environment variable (support both AICORTEX and AICHAT for compatibility)
        env_path = os.environ.get("AICORTEX_CONFIG_DIR") or os.environ.get("AICHAT_CONFIG_DIR")
        if env_path:
            return Path(env_path) / "config.yaml"

        # Use default location
        config_dir = Path.home() / ".config" / "aicortex"
        return config_dir / "config.yaml"

    async def _resolve_model(self, model_id: str) -> Model:
        """Resolve model ID to Model instance.

        Args:
            model_id: Model ID (e.g., "openai:gpt-4")

        Returns:
            Model instance

        Raises:
            ValueError: If model not found
        """
        # Parse provider:model format
        if ":" in model_id:
            provider, model_name = model_id.split(":", 1)
        else:
            provider, model_name = None, model_id

        # Search in clients configuration
        for client in self.clients:
            if provider and client.get("type") != provider:
                continue
            models = client.get("models", [])
            for model_data in models:
                if model_data.get("name") == model_name:
                    return Model(
                        client_name=client.get("type", ""),
                        data=self._dict_to_model_data(model_data),
                    )

        # Create ad-hoc model for known providers
        if provider:
            return Model.new(provider, model_name)

        raise ValueError(f"Model not found: {model_id}")

    def _dict_to_model_data(self, data: dict) -> Any:
        """Convert dict to ModelData.

        Args:
            data: Model data dict

        Returns:
            ModelData instance
        """
        from ..client.model import ModelData

        return ModelData(
            name=data.get("name", ""),
            model_type=data.get("type", "chat"),
            real_name=data.get("real_name"),
            max_input_tokens=data.get("max_input_tokens"),
            max_output_tokens=data.get("max_output_tokens"),
            input_price=data.get("input_price"),
            output_price=data.get("output_price"),
            patch=data.get("patch"),
            require_max_tokens=data.get("require_max_tokens", False),
            supports_vision=data.get("supports_vision", False),
            supports_function_calling=data.get("supports_function_calling", False),
            no_stream=data.get("no_stream", False),
            no_system_message=data.get("no_system_message", False),
            system_prompt_prefix=data.get("system_prompt_prefix"),
            max_tokens_per_chunk=data.get("max_tokens_per_chunk"),
            default_chunk_size=data.get("default_chunk_size"),
            max_batch_size=data.get("max_batch_size"),
        )

    def _update_from_dict(self, data: dict) -> None:
        """Update configuration from dictionary.

        Args:
            data: Configuration dictionary
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _get_default_model(self) -> str:
        """Get default model from configuration.

        Returns:
            Default model ID
        """
        if self.clients and self.clients[0].get("models"):
            client_type = self.clients[0].get("type", "")
            model_name = self.clients[0]["models"][0].get("name", "")
            return f"{client_type}:{model_name}"
        return "openai:gpt-3.5-turbo"

    def extract_role(self) -> Role:
        """Extract current role as Role object.

        Returns:
            Current role or empty role
        """
        if self.role:
            return self.role
        return Role.new("", "")

    def retrieve_role(self, name: str) -> Role:
        """Retrieve a role by name.

        Args:
            name: Role name

        Returns:
            Role instance

        Raises:
            FileNotFoundError: If role not found
        """
        # Try built-in roles first
        try:
            return Role.builtin(name)
        except FileNotFoundError:
            pass

        # Try custom roles from config directory
        role_path = self._get_config_path().parent / "roles" / f"{name}.md"
        if role_path.exists():
            content = role_path.read_text()
            return Role.new(name, content)

        raise FileNotFoundError(f"Role not found: {name}")

    def set_model(self, model_id: str) -> None:
        """Set current model.

        Args:
            model_id: Model ID to set
        """
        self.model_id = model_id
        # Model will be resolved in async context

    def use_role(self, name: str) -> None:
        """Use a specific role.

        Args:
            name: Role name to use
        """
        self.role = self.retrieve_role(name)
        if self.role.model_id:
            self.model_id = self.role.model_id
        self.temperature = self.role.temperature
        self.top_p = self.role.top_p
        self.use_tools = self.role.use_tools

    def use_session(self, name: str) -> None:
        """Use a specific session.

        Args:
            name: Session name to use
        """
        session_dir = self._get_config_path().parent / "sessions"
        session_path = session_dir / f"{name}.yaml"

        if session_path.exists():
            self.session = Session.load(self, name, session_path)
        else:
            self.session = Session.new(self, name)

    def get_client_config(self, client_type: str) -> Optional[dict]:
        """Get client configuration for a specific client type.

        Args:
            client_type: The client type (e.g., "nim", "openai", "claude")

        Returns:
            Client configuration dict or None if not found
        """
        for client in self.clients:
            if client.get("type") == client_type:
                return client
        return None

    def current_model(self) -> Model:
        """Get current model.

        Returns:
            Current model instance
        """
        if self.model is None:
            # Create default model if not set
            self.model = Model.new("openai", "gpt-3.5-turbo")
        return self.model

    def list_all_models(self) -> list[Model]:
        """List all available models from configuration.

        Returns:
            List of all Model instances
        """
        models = []

        for client in self.clients:
            client_type = client.get("type", "")
            for model_data in client.get("models", []):
                models.append(Model(
                    client_name=client_type,
                    data=self._dict_to_model_data(model_data),
                ))

        return models

    def all_roles(self) -> list[str]:
        """Get all available role names.

        Returns:
            List of role names
        """
        roles = []

        # Built-in roles
        roles.extend(["default", "shell", "markdown", "derive", "act",
                      "translate", "polish", "emoji", "sql", "cicd"])

        # Custom roles from config directory
        config_dir = self._get_config_path().parent
        roles_dir = config_dir / "roles"
        if roles_dir.exists():
            for role_file in roles_dir.glob("*.md"):
                roles.append(role_file.stem)

        return list(set(roles))

    def list_rags(self) -> list[str]:
        """List available RAG configurations.

        Returns:
            List of RAG names
        """
        rags = []

        # Check rag directory
        config_dir = self._get_config_path().parent
        rag_dir = config_dir / "rag"
        if rag_dir.exists():
            for rag_file in rag_dir.glob("*.json"):
                rags.append(rag_file.stem)

        return rags

    def agent_functions_dir(self, name: str) -> Path:
        """Get the functions directory for an agent.

        Args:
            name: Agent name

        Returns:
            Path to agent's functions directory
        """
        config_dir = self._get_config_path().parent
        return config_dir / "agents" / name

    def agent_rag_file(self, name: str, rag_type: str = "rag") -> Path:
        """Get the RAG file path for an agent.

        Args:
            name: Agent name
            rag_type: Type of RAG (default: "rag")

        Returns:
            Path to agent's RAG file
        """
        config_dir = self._get_config_path().parent
        rag_dir = config_dir / "rag" / name
        return rag_dir / f"{rag_type}.json"

    def agent_config_file(self, name: str) -> Path:
        """Get the config file path for an agent.

        Args:
            name: Agent name

        Returns:
            Path to agent's config file
        """
        return self.agent_functions_dir(name) / "config.yaml"

    def functions_bin_dir(self) -> Path:
        """Get the functions bin directory.

        Returns:
            Path to functions bin directory
        """
        config_dir = self._get_config_path().parent
        return config_dir / "functions" / "bin"

    def get_serve_addr(self) -> str:
        """Get the server address.

        Returns:
            Server address string
        """
        return self.serve_addr or "127.0.0.1:8000"


__all__ = [
    "Config",
    "WorkingMode",
]
