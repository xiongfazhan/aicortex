"""Variable interpolation utilities.

Corresponds to src/utils/variables.rs in the Rust implementation.
"""

import re
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

# Regular expression for matching {{variable}} patterns
RE_VARIABLE = re.compile(r"\{\{(\w+)\}\}")

# Cache for shell detection
_shell: Optional[str] = None


def get_shell() -> str:
    """Detect current shell.

    Returns:
        Shell name (e.g., "bash", "zsh", "powershell", "cmd")
    """
    global _shell

    if _shell is not None:
        return _shell

    # Check environment variables
    shell_env = os.environ.get("SHELL", "")
    if shell_env:
        _shell = Path(shell_env).stem
        return _shell

    # Windows detection
    if platform.system() == "Windows":
        # Check for PowerShell
        if "PSModulePath" in os.environ:
            _shell = "powershell"
            return _shell
        _shell = "cmd"
        return _shell

    # Default to bash on Unix
    _shell = "bash"
    return _shell


def now() -> str:
    """Get current timestamp in ISO 8601 format.

    Returns:
        Current timestamp string
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def interpolate_variables(text: str) -> str:
    """Replace {{variable}} placeholders with actual values.

    Supported variables:
        __os__: Operating system name
        __os_distro__: OS distribution info
        __os_family__: OS family
        __arch__: System architecture
        __shell__: Current shell
        __locale__: System locale
        __now__: Current timestamp
        __cwd__: Current working directory

    Args:
        text: Text containing variable placeholders

    Returns:
        Text with variables replaced
    """

    def replacer(match: re.Match) -> str:
        key = match.group(1)

        match key:
            case "__os__":
                return platform.system().lower()
            case "__os_distro__":
                import sys
                if platform.system() == "Linux":
                    # Try to get distribution info
                    try:
                        import distro
                        return f"{distro.name()} {distro.version()} (linux)"
                    except ImportError:
                        return f"{platform.release()} (linux)"
                return platform.platform()
            case "__os_family__":
                return os.name
            case "__arch__":
                return platform.machine().lower()
            case "__shell__":
                return get_shell()
            case "__locale__":
                import locale
                loc = locale.getlocale()[0]
                return loc or "en_US.UTF-8"
            case "__now__":
                return now()
            case "__cwd__":
                return os.getcwd()
            case _:
                # Keep unknown variables unchanged
                return f"{{{{{key}}}}}"

    return RE_VARIABLE.sub(replacer, text)


__all__ = [
    "interpolate_variables",
    "get_shell",
    "now",
]
