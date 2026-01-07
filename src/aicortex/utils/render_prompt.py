"""Prompt template rendering utilities.

Corresponds to src/utils/render_prompt.rs in the Rust implementation.

The template syntax:
- {var} - Replace with variable value
- {?var <template>} - Render template if var is truthy
- {!var <template>} - Render template if var is falsy
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional


class BlockType(Enum):
    """Type of conditional block."""

    YES = 1  # {?var ...} - render if truthy
    NO = 2   # {!var ...} - render if falsy


@dataclass
class Expr:
    """A template expression."""

    pass


@dataclass
class TextExpr(Expr):
    """Plain text expression."""

    value: str


@dataclass
class VariableExpr(Expr):
    """Variable reference expression."""

    name: str


@dataclass
class BlockExpr(Expr):
    """Conditional block expression."""

    block_type: BlockType
    variable: str
    exprs: list[Expr]


def render_prompt(template: str, variables: dict[str, str]) -> str:
    """Render a prompt template with variable substitution.

    Args:
        template: Template string with {var} placeholders
        variables: Dictionary of variable names to values

    Returns:
        Rendered string

    Examples:
        >>> render_prompt("Hello {name}", {"name": "World"})
        'Hello World'
        >>> render_prompt("{?show Yes}", {"show": "1"})
        'Yes'
        >>> render_prompt("{!show No}", {"show": "0"})
        'No'
    """
    exprs = parse_template(template)
    return eval_exprs(exprs, variables)


def parse_template(template: str) -> list[Expr]:
    """Parse a template string into expressions.

    Args:
        template: Template string to parse

    Returns:
        List of parsed expressions
    """
    exprs: list[Expr] = []
    current: list[str] = []
    balances: list[str] = []

    for ch in template:
        if balances:
            if ch == "}":
                balances.pop()
                if not balances:
                    if current:
                        block = parse_block("".join(current))
                        exprs.append(block)
                    current = []
                else:
                    current.append(ch)
            elif ch == "{":
                balances.append(ch)
                current.append(ch)
            else:
                current.append(ch)
        elif ch == "{":
            balances.append(ch)
            if current:
                exprs.append(TextExpr("".join(current)))
                current = []
        else:
            current.append(ch)

    if current:
        exprs.append(TextExpr("".join(current)))

    return exprs


def parse_block(value: str) -> Expr:
    """Parse a block expression.

    Args:
        value: Block content without outer braces

    Returns:
        Parsed expression
    """
    parts = value.split(" ", 1)

    if len(parts) == 1:
        # Simple variable: {var}
        var_name = parts[0]
        return VariableExpr(var_name)

    # Check for conditional: {?var ...} or {!var ...}
    var_part = parts[0]
    rest = parts[1]

    if var_part.startswith("?"):
        var_name = var_part[1:]
        block_exprs = parse_template(rest)
        return BlockExpr(BlockType.YES, var_name, block_exprs)

    if var_part.startswith("!"):
        var_name = var_part[1:]
        block_exprs = parse_template(rest)
        return BlockExpr(BlockType.NO, var_name, block_exprs)

    # Unknown syntax, treat as literal
    return TextExpr("{" + value + "}")


def eval_exprs(exprs: list[Expr], variables: dict[str, str]) -> str:
    """Evaluate a list of expressions.

    Args:
        exprs: List of expressions to evaluate
        variables: Variable values

    Returns:
        Evaluated string
    """
    output: list[str] = []

    for expr in exprs:
        if isinstance(expr, TextExpr):
            output.append(expr.value)
        elif isinstance(expr, VariableExpr):
            value = variables.get(expr.name, "")
            output.append(value)
        elif isinstance(expr, BlockExpr):
            value = variables.get(expr.variable, "")
            should_render = _truly(value)

            if expr.block_type == BlockType.NO:
                should_render = not should_render

            if should_render:
                block_output = eval_exprs(expr.exprs, variables)
                output.append(block_output)

    return "".join(output)


def _truly(value: str) -> bool:
    """Check if a string value is truthy.

    Args:
        value: String value to check

    Returns:
        True if value is truthy

    Examples:
        >>> _truly("yes")
        True
        >>> _truly("")
        False
        >>> _truly("0")
        False
        >>> _truly("false")
        False
    """
    return bool(value) and value not in ("0", "false", "no", "none")


def render_prompt_simple(template: str, variables: dict[str, str]) -> str:
    """Simple prompt rendering using regex substitution.

    This is a fallback for simple cases without conditionals.

    Args:
        template: Template string
        variables: Variable values

    Returns:
        Rendered string
    """
    result = template

    # Simple variable substitution: {var}
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", value)

    # Remove undefined variables
    result = re.sub(r"\{[^{}]+\}", "", result)

    return result


__all__ = [
    "BlockType",
    "TextExpr",
    "VariableExpr",
    "BlockExpr",
    "render_prompt",
    "parse_template",
    "eval_exprs",
    "render_prompt_simple",
]
