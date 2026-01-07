"""Macro system for defining reusable command sequences.

Corresponds to the macro system in src/config/mod.rs of the Rust implementation.
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from collections import OrderedDict


@dataclass
class MacroVariable:
    """A variable definition for a macro.

    Attributes:
        name: Variable name
        rest: Whether this variable captures remaining arguments
        default: Default value for the variable
    """

    name: str
    rest: bool = False
    default: Optional[str] = None


@dataclass
class Macro:
    """A macro definition.

    Macros are reusable command sequences with variable interpolation.

    Attributes:
        variables: List of variable definitions
        steps: List of command strings to execute
    """

    variables: list[MacroVariable] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    def resolve_variables(self, args: list[str]) -> "OrderedDict[str, str]":
        """Resolve variables from arguments.

        Args:
            args: Argument values

        Returns:
            Dictionary of variable names to values

        Raises:
            ValueError: If required variable is missing
        """
        output = OrderedDict()

        for i, variable in enumerate(self.variables):
            # Get value for this variable
            if variable.rest and i == len(self.variables) - 1:
                # Last variable with rest flag - capture remaining args
                if len(args) > i:
                    value = " ".join(args[i:])
                else:
                    value = variable.default
            else:
                # Normal variable - get positional arg or default
                value = args[i] if i < len(args) else variable.default

            if value is None:
                raise ValueError(f"Missing value for variable '{variable.name}'")

            output[variable.name] = value

        return output

    def usage(self, name: str) -> str:
        """Generate usage string for the macro.

        Args:
            name: Macro name

        Returns:
            Usage string
        """
        parts = [name]

        for i, variable in enumerate(self.variables):
            is_rest = variable.rest and i == len(self.variables) - 1
            has_default = variable.default is not None

            if is_rest and has_default:
                parts.append(f"[{variable.name}]...")
            elif is_rest:
                parts.append(f"<{variable.name}>...")
            elif has_default:
                parts.append(f"[{variable.name}]")
            else:
                parts.append(f"<{variable.name}>")

        return " ".join(parts)

    @classmethod
    def interpolate_command(cls, command: str, variables: "OrderedDict[str, str]") -> str:
        """Interpolate variables into a command string.

        Args:
            command: Command template with {{{var}}} placeholders
            variables: Variable values

        Returns:
            Interpolated command string
        """
        output = command
        for key, value in variables.items():
            output = output.replace(f"{{{key}}}", value)
        return output

    @classmethod
    def load(cls, path: Path) -> "Macro":
        """Load a macro from a YAML file.

        Args:
            path: Path to macro YAML file

        Returns:
            Macro instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Macro not found: {path}")

        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid macro file: {path}")

        # Parse variables
        variables = []
        for var_data in data.get("variables", []):
            var = MacroVariable(
                name=var_data["name"],
                rest=var_data.get("rest", False),
                default=var_data.get("default"),
            )
            variables.append(var)

        # Get steps
        steps = data.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError(f"Invalid steps in macro: {path}")

        return cls(variables=variables, steps=steps)

    def save(self, path: Path) -> None:
        """Save the macro to a YAML file.

        Args:
            path: Path to save to
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "variables": [
                {
                    "name": v.name,
                    "rest": v.rest if v.rest else None,
                    "default": v.default,
                }
                for v in self.variables
            ],
            "steps": self.steps,
        }

        # Remove None values
        def clean_none(d: dict) -> dict:
            return {
                k: v if v is not None else None
                for k, v in d.items()
            }

        cleaned_data = {}
        for k, v in data.items():
            if isinstance(v, list):
                cleaned_data[k] = [clean_none(item) if isinstance(item, dict) else item for item in v]
            elif isinstance(v, dict):
                cleaned_data[k] = clean_none(v)
            else:
                cleaned_data[k] = v

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(cleaned_data, f, default_flow_style=False, sort_keys=False)


class MacroRegistry:
    """Registry for managing macros.

    Attributes:
        macros_dir: Directory containing macro definitions
    """

    def __init__(self, macros_dir: Optional[Path] = None) -> None:
        """Initialize the registry.

        Args:
            macros_dir: Directory containing macro files
        """
        self.macros_dir = macros_dir or Path("macros")

    def has_macro(self, name: str) -> bool:
        """Check if a macro exists.

        Args:
            name: Macro name

        Returns:
            True if macro exists
        """
        path = self.macros_dir / f"{name}.yaml"
        return path.exists()

    def load_macro(self, name: str) -> Macro:
        """Load a macro by name.

        Args:
            name: Macro name

        Returns:
            Macro instance

        Raises:
            FileNotFoundError: If macro doesn't exist
        """
        path = self.macros_dir / f"{name}.yaml"
        return Macro.load(path)

    def save_macro(self, name: str, macro: Macro) -> None:
        """Save a macro.

        Args:
            name: Macro name
            macro: Macro instance
        """
        path = self.macros_dir / f"{name}.yaml"
        macro.save(path)

    def list_macros(self) -> list[str]:
        """List all available macros.

        Returns:
            List of macro names
        """
        if not self.macros_dir.exists():
            return []

        macros = []
        for path in self.macros_dir.glob("*.yaml"):
            macros.append(path.stem)
        return sorted(macros)

    def delete_macro(self, name: str) -> bool:
        """Delete a macro.

        Args:
            name: Macro name

        Returns:
            True if deleted, False if didn't exist
        """
        path = self.macros_dir / f"{name}.yaml"
        if path.exists():
            path.unlink()
            return True
        return False


__all__ = [
    "MacroVariable",
    "Macro",
    "MacroRegistry",
]
