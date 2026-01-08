"""Command-line interface using Typer.

Corresponds to src/cli.rs in the Rust implementation.
"""

# Fix Windows console encoding for UTF-8 output (must be first)
import sys
import io
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import typer
from typing import Optional

app = typer.Typer(help="AICortex - All-in-one LLM CLI Tool")


@app.command()
def main(
    text: Optional[str] = typer.Argument(None, help="Input text"),
    file: list[str] = typer.Option([], "--file", "-f", help="Input files"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    role: Optional[str] = typer.Option(None, "--role", help="Role to use"),
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Session name"),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Set prompt"),
    rag: Optional[str] = typer.Option(None, "--rag", help="RAG name"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Agent name"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Shell execute mode"),
    code: bool = typer.Option(False, "--code", "-c", help="Code mode"),
    serve: Optional[str] = typer.Option(None, "--serve", help="Start HTTP server"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run mode"),
    list_models: bool = typer.Option(False, "--list-models", help="List models"),
    list_roles: bool = typer.Option(False, "--list-roles", help="List roles"),
    list_sessions: bool = typer.Option(False, "--list-sessions", help="List sessions"),
    list_rags: bool = typer.Option(False, "--list-rags", help="List RAGs"),
    list_agents: bool = typer.Option(False, "--list-agents", help="List agents"),
    info: bool = typer.Option(False, "--info", help="Show info"),
):
    """AICortex CLI - All-in-one LLM CLI Tool

    Interact with Large Language Models from multiple providers.
    """
    asyncio.run(_main(
        text=text,
        file=file,
        model=model,
        role=role,
        session=session,
        prompt=prompt,
        rag=rag,
        agent=agent,
        execute=execute,
        code=code,
        serve=serve,
        no_stream=no_stream,
        dry_run=dry_run,
        list_models=list_models,
        list_roles=list_roles,
        list_sessions=list_sessions,
        list_rags=list_rags,
        list_agents=list_agents,
        info=info,
    ))


async def _main(
    text: Optional[str],
    file: list[str],
    model: Optional[str],
    role: Optional[str],
    session: Optional[str],
    prompt: Optional[str],
    rag: Optional[str],
    agent: Optional[str],
    execute: bool,
    code: bool,
    serve: Optional[str],
    no_stream: bool,
    dry_run: bool,
    list_models: bool,
    list_roles: bool,
    list_sessions: bool,
    list_rags: bool,
    list_agents: bool,
    info: bool,
) -> None:
    """Async main implementation."""
    try:
        from .config import Config, WorkingMode

        # Determine working mode
        if serve is not None:
            working_mode = WorkingMode.SERVE
        elif text is None and not file:
            working_mode = WorkingMode.REPL
        else:
            working_mode = WorkingMode.CMD

        # Initialize configuration
        config = await Config.init(working_mode)

        # Handle list commands
        if list_models:
            await _list_models(config)
            return

        if list_roles:
            _list_roles(config)
            return

        if list_sessions:
            _list_sessions(config)
            return

        if list_rags:
            _list_rags(config)
            return

        if list_agents:
            _list_agents(config)
            return

        if info:
            _show_info(config)
            return

        # Apply configuration
        if model:
            config.set_model(model)

        if no_stream:
            config.stream = False

        if dry_run:
            config.dry_run = True

        # Execute based on mode
        if working_mode == WorkingMode.SERVE:
            await _run_server(config, serve)
        elif working_mode == WorkingMode.REPL:
            await _run_repl(config)
        else:  # CMD mode
            await _run_cmd_mode(config, text, file)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("使用 `--help` 查看用法", file=sys.stderr)
        sys.exit(1)


async def _list_models(config: "Config") -> None:
    """List available models."""
    print("Available models:")
    for client in config.clients:
        client_type = client.get("type", "")
        models = client.get("models", [])
        for model_data in models:
            name = model_data.get("name", "")
            print(f"  {client_type}:{name}")


def _list_roles(config: "Config") -> None:
    """List available roles."""
    from .config.role import Role

    roles = Role.list_builtin_role_names()
    print("Available roles:")
    for role_name in roles:
        print(f"  {role_name}")


def _list_sessions(config: "Config") -> None:
    """List available sessions."""
    session_dir = config._get_config_path().parent / "sessions"
    if session_dir.exists():
        sessions = list(session_dir.glob("*.yaml"))
        print("Available sessions:")
        for session_path in sessions:
            print(f"  {session_path.stem}")
    else:
        print("No sessions found.")


async def _run_cmd_mode(config: "Config", text: Optional[str], files: list[str]) -> None:
    """Run in CMD mode (single query).

    Args:
        config: Configuration
        text: Input text
        files: Input files
    """
    if not text and not files:
        print("Error: No input provided", file=sys.stderr)
        print("可直接运行 `aicortex` 进入 REPL", file=sys.stderr)
        print("或使用 `aicortex '你的问题'`", file=sys.stderr)
        sys.exit(1)

    # Build input from files if provided
    file_content = ""
    if files:
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content += f"\n--- {file_path} ---\n{f.read()}\n"
            except Exception as e:
                print(f"Error reading file {file_path}: {e}", file=sys.stderr)

    # Combine text and file content
    input_text = text or ""
    if file_content:
        input_text = f"{text}\n{file_content}" if text else file_content

    try:
        # Get current model and client
        model = config.current_model()

        # Create client based on model type
        from .llm import create_client, run_chat_completion
        from .client import Message, MessageRole

        # Get API key from environment or config
        import os
        api_key = os.environ.get("API_KEY") or os.environ.get(
            f"{model.client_name.upper()}_API_KEY", ""
        )

        # If not in environment, check config file
        if not api_key:
            client_config = config.get_client_config(model.client_name)
            if client_config:
                config_key = client_config.get("api_key", "")
                # Expand environment variables in the key (e.g., ${NVIDIA_API_KEY})
                if config_key and isinstance(config_key, str):
                    if config_key.startswith("${") and config_key.endswith("}"):
                        env_var = config_key[2:-1]
                        api_key = os.environ.get(env_var, "")
                    else:
                        api_key = config_key

        if not api_key:
            print(f"Error: API key not found for {model.client_name}", file=sys.stderr)
            print(f"Please set {model.client_name.upper()}_API_KEY environment variable", file=sys.stderr)
            print(f"Or add api_key to the {model.client_name} client in config.yaml", file=sys.stderr)
            sys.exit(1)

        # Create client
        client = await create_client(
            client_type=model.client_name,
            api_key=api_key,
            model=model,
        )

        # Build message
        messages = [Message.new(MessageRole.USER, input_text)]

        # Run chat completion
        response = await run_chat_completion(
            client=client,
            messages=messages,
            stream=config.stream,
            temperature=config.temperature,
            top_p=config.top_p,
        )

        # Close client
        await client.close()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("使用 `--help` 查看用法", file=sys.stderr)
        sys.exit(1)


async def _run_server(config: "Config", addr: Optional[str]) -> None:
    """Run HTTP server mode.

    Args:
        config: Configuration
        addr: Server address
    """
    from .serve import run

    await run(config, addr)


async def _run_repl(config: "Config") -> None:
    """Run REPL mode.

    Args:
        config: Configuration
    """
    from .repl import Repl

    repl = Repl(config)
    await repl.run()


def _list_rags(config: "Config") -> None:
    """List available RAG configurations.

    Args:
        config: Configuration
    """
    rags = config.list_rags()
    print("Available RAG configurations:")
    for rag_name in rags:
        print(f"  {rag_name}")
    if not rags:
        print("  No RAG configurations found.")


def _list_agents(config: "Config") -> None:
    """List available agents.

    Args:
        config: Configuration
    """
    config_dir = config._get_config_path().parent
    agents_dir = config_dir / "agents"

    if agents_dir.exists():
        agents = [d.name for d in agents_dir.iterdir() if d.is_dir()]
        print("Available agents:")
        for agent_name in agents:
            print(f"  {agent_name}")
        if not agents:
            print("  No agents found.")
    else:
        print("No agents directory found.")


def _show_info(config: "Config") -> None:
    """Show configuration information.

    Args:
        config: Configuration
    """
    print("AICortex Configuration:")
    print(f"  Model: {config.model_id}")
    print(f"  Temperature: {config.temperature}")
    print(f"  Top P: {config.top_p}")
    print(f"  Stream: {config.stream}")
    print(f"  Dry Run: {config.dry_run}")
    print(f"  Working Mode: {config.working_mode.value}")
    print(f"  Config Path: {config._get_config_path()}")


__all__ = ["app", "main"]
