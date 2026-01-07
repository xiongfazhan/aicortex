"""Path utilities.

Corresponds to src/utils/path.rs in the Rust implementation.
"""

from pathlib import Path
from typing import Optional
import platform
import os
import re
import fnmatch


def safe_join_path(base_path: Path | str, sub_path: Path | str) -> Optional[Path]:
    """Safely join paths, preventing directory traversal attacks.

    Args:
        base_path: The base directory path
        sub_path: The sub path to join (must be relative)

    Returns:
        The joined path, or None if sub_path is absolute or contains '..'
    """
    base_path = Path(base_path)
    sub_path = Path(sub_path)

    # Reject absolute paths
    if sub_path.is_absolute():
        return None

    # Check for parent directory components
    if ".." in sub_path.parts:
        return None

    joined_path = base_path / sub_path

    # Ensure result is within base_path
    try:
        joined_path.resolve().relative_to(base_path.resolve())
        return joined_path
    except ValueError:
        return None


def expand_glob_paths(
    paths: list[str | Path],
    bail_non_exist: bool = False,
) -> list[str]:
    """Expand glob patterns to list of file paths.

    Args:
        paths: List of paths, possibly containing glob patterns
        bail_non_exist: Raise error if path doesn't exist

    Returns:
        List of expanded file paths (deduplicated)
    """
    import asyncio
    return asyncio.run(_expand_glob_paths_async(paths, bail_non_exist))


async def _expand_glob_paths_async(
    paths: list[str | Path],
    bail_non_exist: bool,
) -> list[str]:
    """Async implementation of expand_glob_paths."""
    result: set[str] = set()

    for path in paths:
        path_str, suffixes, current_only = parse_glob(str(path))

        await list_files(
            result,
            Path(path_str),
            suffixes,
            current_only,
            bail_non_exist,
        )

    return sorted(result)


def parse_glob(path_str: str) -> tuple[str, Optional[list[str]], bool]:
    """Parse a glob pattern.

    Returns:
        Tuple of (base_path, extensions, current_only)

    Examples:
        "dir/**/*.md" -> ("dir", ["md"], False)
        "dir/*.{md,txt}" -> ("dir", ["md", "txt"], True)
        "*.py" -> (".", ["py"], True)
    """
    # Try recursive patterns first
    for pattern, offset, current_only in [
        (r"/\*\*/\*\.", 6, False),  # /**/*.
        (r"\*\*/\*\.", 5, False),   # **/*.
        (r"/\*\*\.", 3, True),      # /**.
        (r"\*\*\.", 3, True),       # **.
    ]:
        if pattern in path_str:
            start = path_str.index(pattern)
            base_path = path_str[:start] or "."
            rest = path_str[start + offset:]
            extensions = _parse_extensions(rest)
            return (base_path, extensions, current_only)

    # Try single-level patterns
    for pattern, offset, current_only in [
        (r"/\*\.", 2, True),   # /*.
        (r"\*\.", 1, True),    # *.
    ]:
        if pattern in path_str:
            start = path_str.index(pattern)
            base_path = path_str[:start] or "."
            rest = path_str[start + offset:]
            extensions = _parse_extensions(rest)
            return (base_path, extensions, current_only)

    # Check for recursive directory pattern (no extension)
    if path_str.endswith("/**") or path_str.endswith(r"\**"):
        return (path_str[:-3], None, False)

    # No glob pattern
    return (path_str, None, False)


def _parse_extensions(s: str) -> Optional[list[str]]:
    """Parse extensions from glob pattern.

    Examples:
        "md" -> ["md"]
        "{md,txt}" -> ["md", "txt"]
        "" -> None
    """
    if not s:
        return None

    if s.startswith("{") and s.endswith("}"):
        extensions = s[1:-1].split(",")
        return [e.strip() for e in extensions if e.strip()]

    return [s] if s else None


async def list_files(
    files: set[str],
    entry_path: Path,
    suffixes: Optional[list[str]],
    current_only: bool,
    bail_non_exist: bool,
) -> None:
    """Recursively list files matching criteria.

    Args:
        files: Set to accumulate found file paths
        entry_path: Path to start listing from
        suffixes: Optional list of file extensions to filter
        current_only: Only search current directory (no recursion)
        bail_non_exist: Raise error if entry_path doesn't exist
    """
    if not entry_path.exists():
        if bail_non_exist:
            raise FileNotFoundError(f"Not found '{entry_path}'")
        return

    if entry_path.is_dir():
        import asyncio

        tasks = []
        for entry in entry_path.iterdir():
            if entry.is_dir():
                if not current_only:
                    tasks.append(
                        list_files(files, entry, suffixes, current_only, bail_non_exist)
                    )
            else:
                add_file(files, suffixes, entry)

        await asyncio.gather(*tasks)
    else:
        add_file(files, suffixes, entry_path)


def add_file(files: set[str], suffixes: Optional[list[str]], path: Path) -> None:
    """Add file to set if it matches extension filter."""
    if is_valid_extension(suffixes, path):
        files.add(str(path))


def is_valid_extension(suffixes: Optional[list[str]], path: Path) -> bool:
    """Check if file has valid extension."""
    if not suffixes:
        return True

    ext = path.suffix.lstrip(".").lower()
    return ext in suffixes


def list_file_names(dir_path: Path | str, ext: str) -> list[str]:
    """List files in directory with given extension.

    Args:
        dir_path: Directory path
        ext: File extension (e.g., ".md")

    Returns:
        Sorted list of filenames without the extension
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        return []

    names = []
    for entry in dir_path.iterdir():
        if entry.is_file():
            name = entry.name
            if name.endswith(ext):
                names.append(name[: -len(ext)])

    return sorted(names)


def get_patch_extension(path: str) -> Optional[str]:
    """Get file extension in lowercase.

    Args:
        path: File path

    Returns:
        Lowercase extension without dot, or None
    """
    ext = Path(path).suffix
    return ext.lstrip(".").lower() if ext else None


def to_absolute_path(path: str) -> str:
    """Convert path to absolute path.

    Args:
        path: Input path

    Returns:
        Absolute path as string
    """
    return str(Path(path).resolve())


def resolve_home_dir(path: str) -> str:
    """Expand ~ to home directory.

    Args:
        path: Path potentially containing ~

    Returns:
        Path with ~ expanded
    """
    if path.startswith("~/") or path.startswith("~\\"):
        home = Path.home()
        return str(home / path[2:])
    return path


__all__ = [
    "safe_join_path",
    "expand_glob_paths",
    "parse_glob",
    "list_file_names",
    "get_patch_extension",
    "to_absolute_path",
    "resolve_home_dir",
]
