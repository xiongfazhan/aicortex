"""Agent system for managing AI workflows.

Corresponds to src/config/agent.rs in the Rust implementation.
"""

import os
import yaml
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from collections import OrderedDict

TypeAgentVariables = "OrderedDict[str, str]"


@dataclass
class AgentVariable:
    """Agent variable definition.

    Attributes:
        name: Variable name
        description: Variable description
        default: Default value
    """

    name: str
    description: str
    default: Optional[str] = None


@dataclass
class AgentDefinition:
    """Agent definition from index.yaml.

    Attributes:
        name: Agent name
        description: Agent description
        version: Agent version
        instructions: Base instructions
        dynamic_instructions: Whether instructions are dynamically generated
        variables: Variable definitions
        conversation_starters: Conversation starter prompts
        documents: Document paths for RAG
    """

    name: str = ""
    description: str = ""
    version: str = ""
    instructions: str = ""
    dynamic_instructions: bool = False
    variables: list[AgentVariable] = field(default_factory=list)
    conversation_starters: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "AgentDefinition":
        """Load agent definition from file.

        Args:
            path: Path to index.yaml

        Returns:
            AgentDefinition instance
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        variables = []
        for var_data in data.get("variables", []):
            variables.append(
                AgentVariable(
                    name=var_data["name"],
                    description=var_data.get("description", ""),
                    default=var_data.get("default"),
                )
            )

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", ""),
            instructions=data.get("instructions", ""),
            dynamic_instructions=data.get("dynamic_instructions", False),
            variables=variables,
            conversation_starters=data.get("conversation_starters", []),
            documents=data.get("documents", []),
        )

    def banner(self) -> str:
        """Generate agent banner.

        Returns:
            Banner text
        """
        starters = ""
        if self.conversation_starters:
            starters_list = "\n".join(f"- {s}" for s in self.conversation_starters)
            starters = f"\n\n## Conversation Starters\n{starters_list}"

        return f"# {self.name} {self.version}\n{self.description}{starters}"

    def replace_tools_placeholder(self, functions: Any) -> None:
        """Replace {{__tools__}} placeholder in instructions.

        Args:
            functions: Functions collection
        """
        placeholder = "{{__tools__}}"
        if placeholder in self.instructions:
            tools = []
            for i, func in enumerate(functions.declarations_list(), 1):
                # Get first line of description
                desc = func.description.split("\n")[0] if func.description else ""
                tools.append(f"{i}. {func.name}: {desc}")

            tools_text = "\n".join(tools)
            self.instructions = self.instructions.replace(placeholder, tools_text)


@dataclass
class AgentConfig:
    """Agent configuration.

    Attributes:
        model_id: Model to use
        temperature: Temperature setting
        top_p: Top P setting
        use_tools: Tools mode
        agent_prelude: Agent prelude text
        instructions: Override instructions
        variables: Configuration variables
    """

    model_id: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    use_tools: Optional[str] = None
    agent_prelude: Optional[str] = None
    instructions: Optional[str] = None
    variables: "OrderedDict[str, str]" = field(default_factory=OrderedDict)

    @classmethod
    def new(cls, config: Any) -> "AgentConfig":
        """Create new AgentConfig from global config.

        Args:
            config: Global configuration

        Returns:
            New AgentConfig instance
        """
        return cls(
            use_tools=getattr(config, "use_tools", None),
            agent_prelude=getattr(config, "agent_prelude", None),
        )

    @classmethod
    def load(cls, path: Path) -> "AgentConfig":
        """Load agent config from file.

        Args:
            path: Path to config file

        Returns:
            AgentConfig instance
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(
            model_id=data.get("model"),
            temperature=data.get("temperature"),
            top_p=data.get("top_p"),
            use_tools=data.get("use_tools"),
            agent_prelude=data.get("agent_prelude"),
            instructions=data.get("instructions"),
            variables=OrderedDict(data.get("variables", {})),
        )

    def load_envs(self, name: str) -> None:
        """Load configuration from environment variables.

        Args:
            name: Agent name
        """
        prefix = f"{name}_".upper().replace("-", "_")

        def get_env(key: str, parser=str):
            val = os.environ.get(f"{prefix}{key}")
            if val:
                try:
                    return parser(val)
                except (ValueError, TypeError):
                    return None
            return None

        if v := get_env("MODEL"):
            self.model_id = v
        if v := get_env("TEMPERATURE", float):
            self.temperature = v
        if v := get_env("TOP_P", float):
            self.top_p = v
        if v := get_env("USE_TOOLS"):
            self.use_tools = v
        if v := get_env("AGENT_PRELUDE"):
            self.agent_prelude = v
        if v := get_env("INSTRUCTIONS"):
            self.instructions = v
        if v := os.environ.get(f"{prefix}VARIABLES"):
            try:
                self.variables = OrderedDict(json.loads(v))
            except json.JSONDecodeError:
                pass


@dataclass
class Agent:
    """Agent instance.

    Attributes:
        name: Agent name
        config: Agent configuration
        definition: Agent definition
        shared_variables: Shared variable values
        session_variables: Session-specific variable values
        shared_dynamic_instructions: Cached dynamic instructions
        session_dynamic_instructions: Session dynamic instructions
        functions: Available functions
        rag: Optional RAG instance
        model: Model to use
    """

    name: str
    config: AgentConfig
    definition: AgentDefinition
    shared_variables: "OrderedDict[str, str]" = field(default_factory=OrderedDict)
    session_variables: Optional["OrderedDict[str, str]"] = None
    shared_dynamic_instructions: Optional[str] = None
    session_dynamic_instructions: Optional[str] = None
    functions: Any = None
    rag: Any = None
    model: Any = None

    @classmethod
    async def init(cls, config: Any, name: str, abort_signal: Any = None) -> "Agent":
        """Initialize an agent.

        Args:
            config: Global configuration
            name: Agent name
            abort_signal: Abort signal for async operations

        Returns:
            Agent instance
        """
        # Try to import dynamically to avoid circular imports
        try:
            from .function import Functions
            from .rag import Rag
            from .client import Model
            from .utils import is_url
        except ImportError:
            Functions = None
            Rag = None
            Model = None
            is_url = lambda x: x.startswith(("http://", "https://"))

        functions_dir = Config.agent_functions_dir(name) if Config else Path("agents") / name
        definition_file = functions_dir / "index.yaml"
        functions_file = functions_dir / "functions.json"
        rag_path = Config.agent_rag_file(name, "rag") if Config else None
        config_path = Config.agent_config_file(name) if Config else None

        if not definition_file.exists():
            raise ValueError(f"Unknown agent `{name}`")

        # Load definition
        definition = AgentDefinition.load(definition_file)

        # Load or create config
        if config_path and config_path.exists():
            agent_config = AgentConfig.load(config_path)
        else:
            agent_config = AgentConfig.new(config)

        # Load functions
        functions = Functions(functions_file) if Functions and functions_file.exists() else None
        if functions and definition:
            definition.replace_tools_placeholder(functions)

        # Load config from environment
        agent_config.load_envs(definition.name)

        # Setup model
        if agent_config.model_id and Model and config:
            model = Model.retrieve_model(config, agent_config.model_id)
        elif config and hasattr(config, "current_model"):
            model = config.current_model()
        else:
            model = None

        # Setup RAG
        rag = None
        if Rag and rag_path and rag_path.exists():
            # Load existing RAG
            if config:
                rag = Rag.load(str(rag_path))
        elif definition.documents and not (config and hasattr(config, "info_flag") and config.info_flag):
            # Would need to initialize RAG here
            pass

        return cls(
            name=name,
            config=agent_config,
            definition=definition,
            functions=functions,
            rag=rag,
            model=model,
        )

    def banner(self) -> str:
        """Get agent banner.

        Returns:
            Banner text
        """
        return self.definition.banner()

    def conversation_starters(self) -> list[str]:
        """Get conversation starters.

        Returns:
            List of starter prompts
        """
        return self.definition.conversation_starters

    def interpolated_instructions(self) -> str:
        """Get instructions with variable substitution.

        Returns:
            Interpolated instructions string
        """
        import re
        from .utils import interpolate_variables

        # Get base instructions
        if self.session_dynamic_instructions:
            output = self.session_dynamic_instructions
        elif self.shared_dynamic_instructions:
            output = self.shared_dynamic_instructions
        elif self.config.instructions:
            output = self.config.instructions
        else:
            output = self.definition.instructions

        # Replace agent variables
        for key, value in self.variables().items():
            output = output.replace(f"{{{{{key}}}}}", value)

        # Replace system variables
        output = interpolate_variables(output)
        return output

    def variables(self) -> "OrderedDict[str, str]":
        """Get active variables.

        Returns:
            Session variables if set, otherwise shared variables
        """
        return self.session_variables if self.session_variables else self.shared_variables

    def variable_envs(self) -> dict[str, str]:
        """Get variables as environment variables.

        Returns:
            Dictionary of env var names to values
        """
        envs = {}
        for key, value in self.variables().items():
            env_name = f"LLM_AGENT_VAR_{_normalize_env_name(key)}"
            envs[env_name] = value
        return envs

    def set_shared_variables(self, variables: "OrderedDict[str, str]") -> None:
        """Set shared variables.

        Args:
            variables: Variable values
        """
        self.shared_variables = variables

    def set_session_variables(self, variables: "OrderedDict[str, str]") -> None:
        """Set session variables.

        Args:
            variables: Variable values
        """
        self.session_variables = variables

    def exit_session(self) -> None:
        """Exit session mode."""
        self.session_variables = None
        self.session_dynamic_instructions = None

    def to_role(self) -> Any:
        """Convert agent to a Role.

        Returns:
            Role instance
        """
        try:
            from .config.role import Role
        except ImportError:
            return None

        prompt = self.interpolated_instructions()
        role = Role.new("", prompt)
        # Sync agent settings to role
        role.temperature = self.config.temperature
        role.top_p = self.config.top_p
        return role


def _normalize_env_name(name: str) -> str:
    """Normalize name for environment variable.

    Args:
        name: Variable name

    Returns:
            Normalized name
    """
    return name.upper().replace("-", "_").replace(" ", "_")


def init_agent_variables(
    agent_variables: list[AgentVariable],
    variables: "OrderedDict[str, str]",
    no_interaction: bool = False,
) -> "OrderedDict[str, str]":
    """Initialize agent variables.

    Args:
        agent_variables: Variable definitions
        variables: Existing variable values
        no_interaction: If True, don't prompt for values

    Returns:
        Variable values dictionary
    """
    output = OrderedDict()

    for var in agent_variables:
        key = var.name
        if key in variables:
            output[key] = variables[key]
        elif var.default:
            output[key] = var.default
        elif not no_interaction:
            # Would need to prompt here in interactive mode
            raise ValueError(f"Required agent variable not set: {key}")

    return output


__all__ = [
    "AgentVariable",
    "AgentDefinition",
    "AgentConfig",
    "Agent",
    "TypeAgentVariables",
    "init_agent_variables",
]
