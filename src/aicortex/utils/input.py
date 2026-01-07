"""Input utilities for interactive prompts.

Corresponds to src/utils/input.rs in the Rust implementation.
"""

import sys
from typing import Optional


def read_single_key(
    valid_chars: list[str],
    default: str,
    prompt: str = ""
) -> str:
    """Read a single key press from stdin without requiring Enter.

    This is a simplified version that works on Unix systems.
    For Windows, falls back to regular input().

    Args:
        valid_chars: List of valid character choices
        default: Default value if Enter is pressed
        prompt: Prompt to display

    Returns:
        The character that was pressed

    Examples:
        >>> choice = read_single_key(['y', 'n'], 'n', 'Continue? [y/N]: ')
    """
    print(prompt, end="", flush=True)

    try:
        if sys.platform == "win32":
            return _read_single_key_windows(valid_chars, default)
        else:
            return _read_single_key_unix(valid_chars, default)
    except (EOFError, KeyboardInterrupt):
        print()  # Print newline on interrupt
        raise


def _read_single_key_unix(valid_chars: list[str], default: str) -> str:
    """Read single key on Unix systems."""
    import tty
    import termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)

            if ch == "\n" or ch == "\r":
                # Enter pressed
                print(default)
                return default
            elif ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt()
            elif ch == "\x04":  # Ctrl+D
                raise EOFError()
            elif ch.lower() in valid_chars:
                print(ch)
                return ch
            # Otherwise, ignore and wait for valid input
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _read_single_key_windows(valid_chars: list[str], default: str) -> str:
    """Read single key on Windows (fallback to regular input)."""
    import msvcrt

    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()

            if ch == "\r" or ch == "\n":
                # Enter pressed
                print(default)
                return default
            elif ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt()
            elif ch.lower() in valid_chars:
                print(ch)
                return ch
            # Otherwise, ignore and wait


def read_line(prompt: str = "", default: str = "") -> str:
    """Read a line of input with an optional default value.

    Args:
        prompt: Prompt to display
        default: Default value if user presses Enter

    Returns:
        The input line or default

    Examples:
        >>> name = read_line("Enter name: ", "guest")
    """
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    try:
        line = input(prompt).strip()
        return line if line else default
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def read_password(prompt: str = "Password: ") -> str:
    """Read a password without echoing input.

    Args:
        prompt: Prompt to display

    Returns:
        The password string

    Examples:
        >>> pwd = read_password("Enter password: ")
    """
    try:
        import getpass
        return getpass.getpass(prompt)
    except ImportError:
        # Fallback to regular input
        return input(prompt)


def confirm(prompt: str, default: bool = False) -> bool:
    """Ask a yes/no confirmation question.

    Args:
        prompt: Question to ask
        default: Default answer if user presses Enter

    Returns:
        True if user confirmed, False otherwise

    Examples:
        >>> if confirm("Continue?", default=True):
        ...     print("Continuing...")
    """
    valid_yes = ["y", "yes"]
    valid_no = ["n", "no"]
    default_str = "Y/n" if default else "y/N"

    while True:
        try:
            response = read_line(f"{prompt} [{default_str}]", "").lower()
            if not response:
                return default
            if response in valid_yes:
                return True
            if response in valid_no:
                return False
            print("Please enter 'y' or 'n'")
        except (EOFError, KeyboardInterrupt):
            print()
            return default


def select(prompt: str, options: list[str], default: Optional[int] = None) -> int:
    """Ask user to select from a list of options.

    Args:
        prompt: Prompt to display
        options: List of option strings
        default: Default index if user presses Enter

    Returns:
        Selected index (0-based)

    Examples:
        >>> choice = select("Choose:", ["A", "B", "C"], default=0)
    """
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")

    default_str = f" (default: {default + 1})" if default is not None else ""

    while True:
        try:
            response = read_line(f"{prompt}{default_str}", "").strip()
            if not response and default is not None:
                return default

            try:
                index = int(response) - 1
                if 0 <= index < len(options):
                    return index
                print(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            print()
            if default is not None:
                return default
            raise


__all__ = [
    "read_single_key",
    "read_line",
    "read_password",
    "confirm",
    "select",
]
