"""Markdown rendering with syntax highlighting.

Corresponds to src/render/markdown.rs in the Rust implementation.
"""

import re
import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename, MarkdownLexer
    from pygments.formatters import Terminal256Formatter
    from pygments.style import Style
    from pygments.token import STANDARD_TYPES
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class LineType(Enum):
    """Type of line in markdown output."""

    NORMAL = "normal"
    CODE_BEGIN = "code_begin"
    CODE_INNER = "code_inner"
    CODE_END = "code_end"


@dataclass
class RenderOptions:
    """Options for markdown rendering.

    Attributes:
        theme: Pygments style name
        wrap: Wrap width ("auto" or number)
        wrap_code: Whether to wrap code blocks
        truecolor: Use truecolor (unused in Python)
    """

    theme: Optional[str] = None
    wrap: Optional[str] = None
    wrap_code: bool = False
    truecolor: bool = False

    def get_wrap_width(self) -> Optional[int]:
        """Get wrap width in columns.

        Returns:
            Wrap width or None for no wrapping
        """
        if self.wrap is None:
            return None
        terminal_width = shutil.get_terminal_size((80, 24)).columns
        if self.wrap == "auto":
            return terminal_width
        try:
            return min(terminal_width, int(self.wrap))
        except ValueError:
            return None


class MarkdownRender:
    """Markdown renderer with syntax highlighting.

    Renders markdown text with code block highlighting and line wrapping.
    """

    LANG_MAPS = {
        "csharp": "C#",
        "php": "PHP",
        "js": "JavaScript",
        "ts": "TypeScript",
        "py": "Python",
        "rs": "Rust",
        "go": "Go",
        "java": "Java",
        "cpp": "C++",
        "c": "C",
        "sh": "Bash",
        "bash": "Bash",
        "zsh": "Bash",
        "fish": "Fish",
        "yaml": "YAML",
        "yml": "YAML",
        "json": "JSON",
        "xml": "XML",
        "html": "HTML",
        "css": "CSS",
        "sql": "SQL",
    }

    def __init__(self, options: RenderOptions):
        """Initialize the renderer.

        Args:
            options: Render options
        """
        self.options = options
        self.prev_line_type = LineType.NORMAL
        self.code_syntax: Optional[str] = None
        self.wrap_width = options.get_wrap_width()

        # Setup formatter
        self.formatter: Optional[Terminal256Formatter] = None
        if PYGMENTS_AVAILABLE and options.theme:
            try:
                self.formatter = Terminal256Formatter(style=options.theme)
            except Exception:
                pass

    def render(self, text: str) -> str:
        """Render full markdown text.

        Args:
            text: Markdown text to render

        Returns:
            Rendered output
        """
        lines = text.split("\n")
        output_lines = []
        for line in lines:
            output_lines.append(self._render_line_mut(line))
        return "\n".join(output_lines)

    def render_line(self, line: str) -> str:
        """Render a single line (non-mutating).

        Args:
            line: Line to render

        Returns:
            Rendered line
        """
        _, code_syntax, is_code = self._check_line(line)
        if is_code and code_syntax:
            return self._highlight_code_line(line, code_syntax)
        else:
            return self._highlight_line(line, markdown=True)

    def _render_line_mut(self, line: str) -> str:
        """Render a line and update state.

        Args:
            line: Line to render

        Returns:
            Rendered line
        """
        line_type, code_syntax, is_code = self._check_line(line)

        if is_code and code_syntax:
            output = self._highlight_code_line(line, code_syntax)
        else:
            output = self._highlight_line(line, markdown=True)

        self.prev_line_type = line_type
        self.code_syntax = code_syntax
        return output

    def _check_line(self, line: str) -> tuple[LineType, Optional[str], bool]:
        """Determine line type and syntax.

        Args:
            line: Line to check

        Returns:
            Tuple of (line_type, syntax_name, is_code)
        """
        line_type = self.prev_line_type
        code_syntax = self.code_syntax
        is_code = False

        # Check for code fence
        lang = self._detect_code_block(line)
        if lang is not None:
            match line_type:
                case LineType.NORMAL | LineType.CODE_END:
                    line_type = LineType.CODE_BEGIN
                    code_syntax = lang if lang else None
                case LineType.CODE_BEGIN | LineType.CODE_INNER:
                    line_type = LineType.CODE_END
                    code_syntax = None
        else:
            match line_type:
                case LineType.NORMAL:
                    pass
                case LineType.CODE_END:
                    line_type = LineType.NORMAL
                case LineType.CODE_BEGIN:
                    if code_syntax is None:
                        # Try to guess from content
                        code_syntax = self._guess_syntax(line)
                    line_type = LineType.CODE_INNER
                    is_code = True
                case LineType.CODE_INNER:
                    is_code = True

        return line_type, code_syntax, is_code

    def _highlight_line(self, line: str, markdown: bool = False) -> str:
        """Highlight a line.

        Args:
            line: Line to highlight
            markdown: Whether this is markdown

        Returns:
            Highlighted line
        """
        if not PYGMENTS_AVAILABLE or self.formatter is None:
            return self._wrap_line(line, False)

        # Get leading whitespace
        ws = len(line) - len(line.lstrip())
        whitespace = line[:ws]
        trimmed = line[ws:]

        try:
            if markdown:
                lexer = MarkdownLexer()
            else:
                return self._wrap_line(line, False)

            highlighted = highlight(
                trimmed,
                lexer,
                self.formatter
            ).rstrip("\n")

            result = whitespace + highlighted
            return self._wrap_line(result, markdown)
        except Exception:
            return self._wrap_line(line, False)

    def _highlight_code_line(self, line: str, syntax: str) -> str:
        """Highlight a code line.

        Args:
            line: Line to highlight
            syntax: Syntax name

        Returns:
            Highlighted line
        """
        if not PYGMENTS_AVAILABLE or self.formatter is None:
            return self._wrap_line(line, True)

        # Get leading whitespace
        ws = len(line) - len(line.lstrip())
        whitespace = line[:ws]
        trimmed = line[ws:]

        try:
            lexer = get_lexer_by_name(syntax)
            highlighted = highlight(
                trimmed,
                lexer,
                self.formatter
            ).rstrip("\n")

            result = whitespace + highlighted
            return self._wrap_line(result, True)
        except Exception:
            return self._wrap_line(line, True)

    def _wrap_line(self, line: str, is_code: bool) -> str:
        """Wrap line to width.

        Args:
            line: Line to wrap
            is_code: Whether this is code

        Returns:
            Wrapped line
        """
        if self.wrap_width is None:
            return line
        if is_code and not self.options.wrap_code:
            return line

        # Count leading spaces for indent
        indent = len(line) - len(line.lstrip(" "))
        indent_str = line[:indent]

        # Wrap the rest
        rest = line[indent:]
        if not rest:
            return line

        wrapped = []
        current_line = indent_str
        current_length = indent

        for word in rest.split():
            word_length = len(word)
            if current_length + word_length + 1 <= self.wrap_width:
                if current_line != indent_str:
                    current_line += " "
                    current_length += 1
                current_line += word
                current_length += word_length
            else:
                if current_line != indent_str:
                    wrapped.append(current_line)
                current_line = indent_str + "  " + word
                current_length = indent + 2 + word_length

        if current_line != indent_str:
            wrapped.append(current_line)

        return "\n".join(wrapped) if wrapped else line

    def _detect_code_block(self, line: str) -> Optional[str]:
        """Detect code fence and extract language.

        Args:
            line: Line to check

        Returns:
            Language name or None
        """
        stripped = line.lstrip()
        if not stripped.startswith("```"):
            return None

        lang = stripped[3:].strip().split()[0] if stripped[3:] else ""
        return lang

    def _find_syntax(self, lang: str) -> Optional[str]:
        """Find syntax name for language.

        Args:
            lang: Language identifier

        Returns:
            Syntax name or None
        """
        # Check language map
        lang_lower = lang.lower()
        if lang_lower in self.LANG_MAPS:
            return self.LANG_MAPS[lang_lower]

        # Try to get lexer
        if PYGMENTS_AVAILABLE:
            try:
                lexer = get_lexer_by_name(lang)
                return lexer.name
            except Exception:
                pass

        return lang

    def _guess_syntax(self, line: str) -> Optional[str]:
        """Guess syntax from line content.

        Args:
            line: Line to analyze

        Returns:
            Guessed syntax name
        """
        if not PYGMENTS_AVAILABLE:
            return None

        try:
            # Create a fake filename to trigger guessing
            lexer = guess_lexer_for_filename("tmp", line)
            return lexer.name
        except Exception:
            return None


def render_markdown(text: str, options: Optional[RenderOptions] = None) -> str:
    """Render markdown text with highlighting.

    Args:
        text: Markdown text
        options: Render options (default: no theme, no wrap)

    Returns:
        Rendered output
    """
    if options is None:
        options = RenderOptions()

    renderer = MarkdownRender(options)
    return renderer.render(text)


__all__ = [
    "LineType",
    "RenderOptions",
    "MarkdownRender",
    "render_markdown",
]
