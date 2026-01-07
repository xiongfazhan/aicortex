"""Shell command execution utilities.

Corresponds to src/utils/command.rs in the Rust implementation.
"""

import os
import sys
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Shell:
    """Shell configuration.

    Attributes:
        name: Shell name (e.g., "bash", "zsh", "powershell")
        cmd: Shell executable command
        arg: Argument to pass command for execution (e.g., "-c", "-Command")
    """

    name: str
    cmd: str
    arg: str

    @classmethod
    def create(cls, name: str, cmd: str, arg: str) -> "Shell":
        """Create a new Shell instance.

        Args:
            name: Shell name
            cmd: Shell executable command
            arg: Argument for command execution

        Returns:
            Shell instance
        """
        return cls(name=name, cmd=cmd, arg=arg)


def detect_shell() -> Shell:
    """Auto-detect the system shell.

    Returns:
        Detected shell configuration
    """
    # Check environment variable
    env_key = get_env_name("shell")
    cmd = os.environ.get(env_key)

    if not cmd and sys.platform == "win32":
        # Windows-specific detection
        ps_module_path = os.environ.get("PSModulePath", "").lower()
        if ps_module_path.startswith("c:\\users"):
            if "\\powershell\\7" in ps_module_path:
                cmd = "pwsh.exe"
            else:
                cmd = "powershell.exe"

    # Extract shell name
    if cmd:
        cmd_path = Path(cmd)
        name = cmd_path.stem.lower()
        if name == "nu":
            name = "nushell"
    else:
        cmd = None
        name = None

    # Default shells
    if not cmd or not name:
        if sys.platform == "win32":
            cmd = "cmd.exe"
            name = "cmd"
        else:
            cmd = "/bin/sh"
            name = "sh"

    # Determine shell argument
    if name == "powershell" or name == "pwsh":
        shell_arg = "-Command"
    elif name == "cmd":
        shell_arg = "/C"
    else:
        shell_arg = "-c"

    return Shell.create(name, cmd, shell_arg)


def get_env_name(name: str) -> str:
    """Get environment variable name.

    Args:
        name: Variable name suffix

    Returns:
        Environment variable name (uppercase)
    """
    return f"AICHAT_{name}".upper()


def run_command(
    cmd: str,
    args: list[str],
    envs: Optional[dict[str, str]] = None,
) -> int:
    """Run a command and return exit code.

    Args:
        cmd: Command to execute
        args: Command arguments
        envs: Optional environment variables

    Returns:
        Exit code (0 for success)

    Raises:
        IOError: If command fails to execute
    """
    try:
        # Prepare environment
        process_env = os.environ.copy()
        if envs:
            process_env.update(envs)

        # Run command
        result = subprocess.run(
            [cmd] + args,
            env=process_env,
            check=False,
        )
        return result.returncode

    except FileNotFoundError:
        raise IOError(f"Command not found: {cmd}")
    except Exception as e:
        raise IOError(f"Failed to run command: {e}")


def run_command_with_output(
    cmd: str,
    args: list[str],
    envs: Optional[dict[str, str]] = None,
) -> tuple[bool, str, str]:
    """Run a command and capture output.

    Args:
        cmd: Command to execute
        args: Command arguments
        envs: Optional environment variables

    Returns:
        Tuple of (success, stdout, stderr)

    Raises:
        IOError: If command fails to execute
    """
    try:
        # Prepare environment
        process_env = os.environ.copy()
        if envs:
            process_env.update(envs)

        # Run command and capture output
        result = subprocess.run(
            [cmd] + args,
            env=process_env,
            check=False,
            capture_output=True,
            text=True,
        )

        success = result.returncode == 0
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        return (success, stdout, stderr)

    except FileNotFoundError:
        raise IOError(f"Command not found: {cmd}")
    except Exception as e:
        raise IOError(f"Failed to run command: {e}")


def run_loader_command(
    path: str,
    extension: str,
    loader_command: str,
) -> str:
    """Run a document loader command.

    Args:
        path: Path to the file to load
        extension: File extension
        loader_command: Command template (use $1 for input, $2 for output)

    Returns:
        Loaded content

    Raises:
        IOError: If loader fails
    """
    import shlex

    try:
        # Parse command
        cmd_args = shlex.split(loader_command)
    except ValueError as e:
        raise IOError(f"Invalid document loader '{extension}': `{loader_command}`: {e}")

    use_stdout = True
    outpath = ""

    # Replace placeholders
    processed_args = []
    for arg in cmd_args:
        if "$1" in arg:
            arg = arg.replace("$1", path)
        if "$2" in arg:
            use_stdout = False
            # Create temp file for output
            with tempfile.NamedTemporaryFile(
                suffix=f"-{extension}", delete=False
            ) as f:
                outpath = f.name
            arg = arg.replace("$2", outpath)
        processed_args.append(arg)

    cmd_eval = " ".join(shlex.quote(arg) for arg in processed_args)

    if not processed_args:
        raise IOError(f"Empty loader command: `{loader_command}`")

    cmd = processed_args[0]
    args = processed_args[1:]

    try:
        if use_stdout:
            # Capture stdout
            success, stdout, stderr = run_command_with_output(cmd, args, None)

            if not success:
                err = stderr if stderr else f"The command `{cmd_eval}` exited with non-zero."
                raise IOError(err)

            return stdout
        else:
            # Write to output file
            exit_code = run_command(cmd, args, None)

            if exit_code != 0:
                raise IOError(f"The command `{cmd_eval}` exited with non-zero.")

            # Read output file
            try:
                with open(outpath, "r", encoding="utf-8") as f:
                    content = f.read()
                return content
            finally:
                # Clean up temp file
                try:
                    os.unlink(outpath)
                except OSError:
                    pass

    except IOError:
        raise
    except Exception as e:
        raise IOError(f"Unable to run `{cmd_eval}`, perhaps '{cmd}' is not installed: {e}")


def edit_file(editor: str, path: Path) -> None:
    """Open a file in an editor.

    Args:
        editor: Editor command
        path: Path to the file

    Raises:
        IOError: If editor fails to open
    """
    try:
        # Check if editor exists
        editor_cmd = editor.split()[0]  # Handle editor with args like "code -w"
        if not shutil.which(editor_cmd):
            raise IOError(f"Editor not found: {editor_cmd}")

        # Run editor and wait
        result = subprocess.run(
            editor.split() + [str(path)],
            check=False,
        )

        if result.returncode != 0:
            raise IOError(f"Editor exited with code {result.returncode}")

    except IOError:
        raise
    except Exception as e:
        raise IOError(f"Failed to open editor: {e}")


def append_to_shell_history(
    shell: str,
    command: str,
    exit_code: int,
) -> None:
    """Append a command to shell history.

    Args:
        shell: Shell name
        command: Command to add
        exit_code: Command exit code
    """
    history_file = get_history_file(shell)
    if not history_file:
        return

    try:
        # Normalize command (replace newlines with spaces)
        normalized_cmd = command.replace("\n", " ")

        # Get timestamp
        import time
        now = int(time.time())

        # Format based on shell type
        if shell == "fish":
            history_txt = f"- cmd: {normalized_cmd}\n  when: {now}"
        elif shell == "zsh":
            history_txt = f": {now}:{exit_code};{normalized_cmd}"
        else:
            history_txt = normalized_cmd

        # Create parent directories if needed
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Append to history file
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(history_txt + "\n")

    except (IOError, OSError):
        # Silently fail if we can't write to history
        pass


def get_history_file(shell: str) -> Optional[Path]:
    """Get the history file path for a shell.

    Args:
        shell: Shell name

    Returns:
        Path to history file, or None if not applicable
    """
    home = Path.home()

    match shell:
        case "bash" | "sh":
            # Check HISTFILE environment variable
            histfile = os.environ.get("HISTFILE")
            if histfile:
                return Path(histfile)
            return home / ".bash_history"

        case "zsh":
            histfile = os.environ.get("HISTFILE")
            if histfile:
                return Path(histfile)
            return home / ".zsh_history"

        case "nushell":
            # Linux/macOS: ~/.config/nushell/history.txt
            config_dir = os.environ.get("XDG_CONFIG_HOME", home / ".config")
            return Path(config_dir) / "nushell" / "history.txt"

        case "fish":
            return home / ".local" / "share" / "fish" / "fish_history"

        case "powershell" | "pwsh":
            if sys.platform == "win32":
                # Windows: %LOCALAPPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
                appdata = os.environ.get("LOCALAPPDATA")
                if appdata:
                    return Path(appdata) / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt"
            else:
                # Linux/macOS: ~/.local/share/powershell/PSReadLine/ConsoleHost_history.txt
                return home / ".local" / "share" / "powershell" / "PSReadLine" / "ConsoleHost_history.txt"

        case "ksh":
            return home / ".ksh_history"

        case "tcsh":
            return home / ".history"

        case _:
            return None


# Global shell instance (lazy-loaded)
_sheell_instance: Optional[Shell] = None


def get_shell() -> Shell:
    """Get the global shell instance.

    Returns:
        Detected shell configuration
    """
    global _sheell_instance
    if _sheell_instance is None:
        _sheell_instance = detect_shell()
    return _sheell_instance


__all__ = [
    "Shell",
    "detect_shell",
    "get_shell",
    "run_command",
    "run_command_with_output",
    "run_loader_command",
    "edit_file",
    "append_to_shell_history",
    "get_history_file",
]
