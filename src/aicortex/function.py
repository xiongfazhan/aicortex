"""Function calling and tool use.

Corresponds to src/function.rs in the Rust implementation.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from collections import OrderedDict
from collections.abc import Mapping

try:
    from .config import Config
    from .client import Model
    from .utils import temp_file
except ImportError:
    Config = None
    Model = None
    temp_file = None


@dataclass
class JsonSchema:
    """JSON Schema for function parameters.

    Attributes:
        type_value: Type (string, object, array, etc.)
        description: Parameter description
        properties: Nested properties for objects
        items: Schema for array items
        any_of: AnyOf schemas
        enum_value: Enum values
        default: Default value
        required: Required property names
    """

    type_value: Optional[str] = None
    description: Optional[str] = None
    properties: Optional["OrderedDict[str, JsonSchema]"] = None
    items: Optional["JsonSchema"] = None
    any_of: Optional[list["JsonSchema"]] = None
    enum_value: Optional[list[str]] = None
    default: Optional[Any] = None
    required: Optional[list[str]] = None

    def is_empty_properties(self) -> bool:
        """Check if properties are empty.

        Returns:
            True if no properties or properties list is empty
        """
        return not self.properties

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        result = {}
        if self.type_value:
            result["type"] = self.type_value
        if self.description:
            result["description"] = self.description
        if self.properties:
            result["properties"] = {
                k: v.to_dict() for k, v in self.properties.items()
            }
        if self.items:
            result["items"] = self.items.to_dict()
        if self.any_of:
            result["anyOf"] = [v.to_dict() for v in self.any_of]
        if self.enum_value:
            result["enum"] = self.enum_value
        if self.default is not None:
            result["default"] = self.default
        if self.required:
            result["required"] = self.required
        return result


@dataclass
class FunctionDeclaration:
    """Function/tool declaration.

    Attributes:
        name: Function name
        description: Function description
        parameters: JSON Schema for parameters
        agent: Whether this is an agent function
    """

    name: str
    description: str
    parameters: JsonSchema
    agent: bool = False


@dataclass
class ToolCall:
    """A tool call request.

    Attributes:
        name: Function name to call
        arguments: Function arguments (JSON or string)
        id: Optional call ID
    """

    name: str
    arguments: Any
    id: Optional[str] = None

    @classmethod
    def new(cls, name: str, arguments: Any, id: Optional[str] = None) -> "ToolCall":
        """Create a new ToolCall.

        Args:
            name: Function name
            arguments: Function arguments
            id: Optional call ID

        Returns:
            New ToolCall instance
        """
        return cls(name=name, arguments=arguments, id=id)

    @classmethod
    def dedup(cls, calls: list["ToolCall"]) -> list["ToolCall"]:
        """Remove duplicate calls by ID.

        Args:
            calls: List of tool calls

        Returns:
            Deduplicated list (preserving order)
        """
        seen_ids = set()
        new_calls = []

        for call in reversed(calls):
            if call.id and call.id not in seen_ids:
                seen_ids.add(call.id)
                new_calls.append(call)
            elif not call.id:
                new_calls.append(call)

        new_calls.reverse()
        return new_calls

    def eval(self, config: Any = None) -> Any:
        """Evaluate the tool call.

        Args:
            config: Global configuration

        Returns:
            Tool result (JSON value)

        Raises:
            Exception: If evaluation fails
        """
        call_name, cmd_name, cmd_args, envs = self._extract_call_config(config)

        # Parse arguments
        if isinstance(self.arguments, dict):
            json_data = self.arguments
        elif isinstance(self.arguments, str):
            try:
                json_data = json.loads(self.arguments)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"The call '{call_name}' has invalid arguments: {self.arguments}"
                ) from e
        else:
            raise ValueError(
                f"The call '{call_name}' has invalid arguments: {self.arguments}"
            )

        cmd_args.append(json.dumps(json_data))

        output = run_llm_function(cmd_name, cmd_args, envs)
        return output

    def _extract_call_config(self, config: Any) -> tuple[str, str, list[str], dict[str, str]]:
        """Extract call configuration from config or agent.

        Args:
            config: Global configuration

        Returns:
            Tuple of (call_name, cmd_name, cmd_args, envs)
        """
        function_name = self.name

        # Check if agent is active
        if config and hasattr(config, "agent") and config.agent:
            agent = config.agent
            if hasattr(agent, "functions") and agent.functions.find(function_name):
                function = agent.functions.find(function_name)
                if function.agent:
                    agent_name = agent.name
                    return (
                        f"{agent_name}-{function_name}",
                        agent_name,
                        [function_name],
                        agent.variable_envs(),
                    )
                else:
                    return function_name, function_name, [], {}

        # Check global functions
        if config and hasattr(config, "functions") and config.functions.contains(function_name):
            return function_name, function_name, [], {}

        raise ValueError(f"Unexpected call: {function_name} {self.arguments}")


@dataclass
class ToolResult:
    """Result of a tool call.

    Attributes:
        call: The tool call that was made
        output: Result output
    """

    call: ToolCall
    output: Any

    @classmethod
    def new(cls, call: ToolCall, output: Any) -> "ToolResult":
        """Create a new ToolResult.

        Args:
            call: Tool call
            output: Output value

        Returns:
            New ToolResult instance
        """
        return cls(call=call, output=output)


class Functions:
    """Collection of function declarations.

    Attributes:
        declarations: List of function declarations
    """

    def __init__(self, declarations_path: Optional[Path] = None):
        """Initialize Functions.

        Args:
            declarations_path: Path to functions.json file
        """
        self.declarations: list[FunctionDeclaration] = []

        if declarations_path and declarations_path.exists():
            try:
                content = declarations_path.read_text(encoding="utf-8")
                data = json.loads(content)

                for item in data:
                    params = item.get("parameters", {})
                    schema = JsonSchema(
                        type_value=params.get("type"),
                        description=params.get("description"),
                        required=params.get("required"),
                    )

                    # Build properties
                    if "properties" in params:
                        schema.properties = OrderedDict()
                        for prop_name, prop_data in params["properties"].items():
                            schema.properties[prop_name] = JsonSchema(
                                type_value=prop_data.get("type"),
                                description=prop_data.get("description"),
                            )

                    self.declarations.append(
                        FunctionDeclaration(
                            name=item["name"],
                            description=item["description"],
                            parameters=schema,
                            agent=item.get("agent", False),
                        )
                    )
            except (json.JSONDecodeError, IOError, KeyError) as e:
                # If loading fails, start with empty declarations
                pass

    def find(self, name: str) -> Optional[FunctionDeclaration]:
        """Find a function by name.

        Args:
            name: Function name

        Returns:
            Function declaration or None
        """
        for decl in self.declarations:
            if decl.name == name:
                return decl
        return None

    def contains(self, name: str) -> bool:
        """Check if function exists.

        Args:
            name: Function name

        Returns:
            True if function exists
        """
        return self.find(name) is not None

    def declarations_list(self) -> list[FunctionDeclaration]:
        """Get all declarations.

        Returns:
            List of function declarations
        """
        return self.declarations

    def is_empty(self) -> bool:
        """Check if no functions.

        Returns:
            True if no declarations
        """
        return len(self.declarations) == 0


def eval_tool_calls(config: Any, calls: list[ToolCall]) -> list[ToolResult]:
    """Evaluate tool calls.

    Args:
        config: Global configuration
        calls: List of tool calls

    Returns:
        List of tool results

    Raises:
        Exception: If evaluation fails
    """
    if not calls:
        return []

    # Remove duplicates
    calls = ToolCall.dedup(calls)
    if not calls:
        raise ValueError(
            "The request was aborted because an infinite loop of function calls was detected."
        )

    output = []
    is_all_null = True

    for call in calls:
        try:
            result = call.eval(config)
            if result is None:
                result = "DONE"
            else:
                is_all_null = False
            output.append(ToolResult.new(call, result))
        except Exception as e:
            output.append(ToolResult.new(call, {"error": str(e)}))

    if is_all_null:
        output = []

    return output


def run_llm_function(
    cmd_name: str,
    cmd_args: list[str],
    envs: dict[str, str],
) -> Any:
    """Run an LLM function (external command).

    Args:
        cmd_name: Command name
        cmd_args: Command arguments
        envs: Environment variables

    Returns:
        Command output (parsed JSON or raw string)

    Raises:
        Exception: If command fails
    """
    # Setup environment
    process_env = os.environ.copy()
    process_env.update(envs)

    # Setup PATH
    bin_dirs = []
    if len(cmd_args) > 1 and Config:
        # Try agent-specific bin directory
        agent_bin_dir = Config.agent_functions_dir(cmd_name).joinpath("bin")
        if agent_bin_dir.exists():
            bin_dirs.append(str(agent_bin_dir))

    if Config:
        functions_bin_dir = Config.functions_bin_dir()
        if functions_bin_dir.exists():
            bin_dirs.append(str(functions_bin_dir))

    if bin_dirs:
        path_sep = ";" if os.name == "nt" else ":"
        current_path = process_env.get("PATH", "")
        prepend_path = path_sep.join(bin_dirs + [""])
        process_env["PATH"] = prepend_path + current_path

    # Setup output file
    with tempfile.NamedTemporaryFile(mode="w", suffix="-eval-", delete=False) as f:
        temp_path = f.name
    process_env["LLM_OUTPUT"] = temp_path

    try:
        # Run command
        result = subprocess.run(
            [cmd_name] + cmd_args,
            env=process_env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise Exception(f"Tool call exit with {result.returncode}: {error_msg}")

        # Read output file
        output = None
        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                contents = f.read()
                if contents:
                    try:
                        output = json.loads(contents)
                    except json.JSONDecodeError:
                        output = contents
        except FileNotFoundError:
            pass

        return output if output is not None else None

    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


__all__ = [
    "JsonSchema",
    "FunctionDeclaration",
    "ToolCall",
    "ToolResult",
    "Functions",
    "eval_tool_calls",
    "run_llm_function",
]
