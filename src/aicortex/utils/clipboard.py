"""Clipboard utilities.

Corresponds to src/utils/clipboard.rs in the Rust implementation.
"""

import sys
import subprocess
from typing import Optional


class ClipboardError(Exception):
    """Clipboard operation error."""
    pass


def copy(text: str) -> None:
    """Copy text to clipboard.

    Args:
        text: Text to copy

    Raises:
        ClipboardError: If copy operation fails
    """
    if not text:
        raise ClipboardError("Cannot copy empty text")

    if sys.platform == "win32":
        # Windows: use clip
        try:
            process = subprocess.Popen(
                ["clip"],
                stdin=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            process.communicate(text.encode("utf-16-le"))
            if process.returncode != 0:
                raise ClipboardError("Failed to copy to clipboard")
        except Exception as e:
            raise ClipboardError(f"Failed to copy to clipboard: {e}")

    elif sys.platform == "darwin":
        # macOS: use pbcopy
        try:
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE
            )
            process.communicate(text.encode("utf-8"))
            if process.returncode != 0:
                raise ClipboardError("Failed to copy to clipboard")
        except Exception as e:
            raise ClipboardError(f"Failed to copy to clipboard: {e}")

    else:
        # Linux: try xclip, then wl-copy, then xsel
        commands = [
            ["xclip", "-selection", "clipboard"],
            ["wl-copy"],
            ["xsel", "--clipboard", "--input"]
        ]

        for cmd in commands:
            try:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE
                )
                process.communicate(text.encode("utf-8"))
                if process.returncode == 0:
                    return
            except FileNotFoundError:
                continue
            except Exception as e:
                raise ClipboardError(f"Failed to copy to clipboard: {e}")

        raise ClipboardError(
            "No clipboard utility found. Please install xclip or wl-copy."
        )


def paste() -> Optional[str]:
    """Paste text from clipboard.

    Returns:
        Clipboard content or None if not available

    Raises:
        ClipboardError: If paste operation fails
    """
    if sys.platform == "win32":
        # Windows: use PowerShell
        try:
            result = subprocess.run(
                ["powershell", "-command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                return result.stdout.rstrip("\n")
        except Exception as e:
            raise ClipboardError(f"Failed to paste from clipboard: {e}")

    elif sys.platform == "darwin":
        # macOS: use pbpaste
        try:
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            raise ClipboardError(f"Failed to paste from clipboard: {e}")

    else:
        # Linux: try xclip, then wl-paste, then xsel
        commands = [
            ["xclip", "-selection", "clipboard", "-o"],
            ["wl-paste"],
            ["xsel", "--clipboard", "--output"]
        ]

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout
            except FileNotFoundError:
                continue
            except Exception as e:
                raise ClipboardError(f"Failed to paste from clipboard: {e}")

        return None


def copy_command(command: str) -> None:
    """Copy a shell command to clipboard.

    Args:
        command: Command to copy
    """
    copy(command)


__all__ = ["copy", "paste", "copy_command", "ClipboardError"]
