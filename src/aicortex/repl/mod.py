"""REPL (Read-Eval-Print Loop) module.

Corresponds to src/repl/mod.rs in the Rust implementation.
"""

# Fix Windows console encoding for UTF-8 output (must be first)
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import locale
import os
import re
from dataclasses import dataclass, field
from enum import Flag, auto
from pathlib import Path
from typing import Any, Callable, Optional, Coroutine
from collections import OrderedDict

# Detect system language for Chinese support
try:
    _sys_lang = locale.getdefaultlocale()[0] or locale.getpreferredlanguage() or os.getenv('LANG', '')
    _IS_ZH = _sys_lang.lower().startswith('zh')
except:
    _IS_ZH = False

# Global language setting (can be overridden by user)
_LANGUAGE_SETTING: Optional[str] = None  # 'zh', 'en', or None for auto

def _is_chinese() -> bool:
    """Check if Chinese language should be used.

    Returns:
        True if Chinese should be used, False otherwise
    """
    global _LANGUAGE_SETTING, _IS_ZH
    if _LANGUAGE_SETTING == 'zh':
        return True
    elif _LANGUAGE_SETTING == 'en':
        return False
    else:
        return _IS_ZH

def set_language(lang: str) -> None:
    """Set the language mode.

    Args:
        lang: Language code ('zh', 'en', or 'auto')
    """
    global _LANGUAGE_SETTING
    if lang.lower() in ['zh', 'chinese', '中文']:
        _LANGUAGE_SETTING = 'zh'
    elif lang.lower() in ['en', 'english', '英文']:
        _LANGUAGE_SETTING = 'en'
    elif lang.lower() in ['auto', 'automatic', '自动']:
        _LANGUAGE_SETTING = None
    else:
        raise ValueError(f"Invalid language: {lang}. Use 'zh', 'en', or 'auto'")


def _msg(zh: str, en: str) -> str:
    """Get message based on current language.

    Args:
        zh: Chinese message
        en: English message

    Returns:
        Appropriate message based on current language setting
    """
    return zh if _is_chinese() else en


try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.formatted_text import HTML
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


class StateFlags(Flag):
    """REPL state flags.

    Used to validate which commands are available in different states.
    """

    ROLE = auto()
    SESSION = auto()
    SESSION_EMPTY = auto()
    AGENT = auto()
    RAG = auto()
    MACRO = auto()


@dataclass
class ReplCommand:
    """A REPL command.

    Attributes:
        name: Command name (e.g., ".help")
        description: Command description (English)
        description_zh: Command description (Chinese)
        state_validator: Function to validate if command is available
    """

    name: str
    description: str
    description_zh: str = ""
    state_validator: Callable[[StateFlags], bool] = lambda _: True

    def is_valid(self, flags: StateFlags) -> bool:
        """Check if command is valid in current state.

        Args:
            flags: Current state flags

        Returns:
            True if command is valid
        """
        return self.state_validator(flags)

    def get_description(self) -> str:
        """Get description based on current language.

        Returns:
            Chinese description if in Chinese mode, otherwise English
        """
        if _is_chinese() and self.description_zh:
            return self.description_zh
        return self.description


class Repl:
    """REPL for interactive chat.

    Provides a command-line interface for interacting with LLMs.
    """

    # All REPL commands
    COMMANDS: list[ReplCommand] = [
        ReplCommand(".help", "Show this help guide", "显示此帮助指南"),
        ReplCommand(".info", "Show system info", "显示系统信息"),
        ReplCommand(".model", "Switch LLM model", "切换 LLM 模型"),
        ReplCommand(".prompt", "Set a temporary role using a prompt", "使用提示设置临时角色"),
        ReplCommand(".role", "Create or switch to a role", "创建或切换角色"),
        ReplCommand(".info role", "Show role info", "显示角色信息", lambda f: StateFlags.ROLE in f),
        ReplCommand(".edit role", "Modify current role", "修改当前角色"),
        ReplCommand(".save role", "Save current role to file", "保存当前角色到文件"),
        ReplCommand(".exit role", "Exit active role", "退出当前角色"),
        ReplCommand(".session", "Start or switch to a session", "启动或切换会话"),
        ReplCommand(".empty session", "Clear session messages", "清空会话消息"),
        ReplCommand(".compress session", "Compress session messages", "压缩会话消息"),
        ReplCommand(".info session", "Show session info", "显示会话信息"),
        ReplCommand(".edit session", "Modify current session", "修改当前会话"),
        ReplCommand(".save session", "Save current session to file", "保存当前会话到文件"),
        ReplCommand(".exit session", "Exit active session", "退出当前会话"),
        ReplCommand(".rag", "Initialize or access RAG", "初始化或访问 RAG"),
        ReplCommand(".edit rag-docs", "Add or remove documents from RAG", "添加或删除 RAG 文档"),
        ReplCommand(".rebuild rag", "Rebuild RAG for document changes", "重建 RAG（文档更改后）"),
        ReplCommand(".sources rag", "Show citation sources used in last query", "显示上次查询的引用来源"),
        ReplCommand(".info rag", "Show RAG info", "显示 RAG 信息"),
        ReplCommand(".exit rag", "Leave RAG", "离开 RAG"),
        ReplCommand(".file", "Include files, directories, or URLs", "包含文件、目录或 URL"),
        ReplCommand(".continue", "Continue previous response", "继续上一个响应"),
        ReplCommand(".regenerate", "Regenerate last response", "重新生成上一个响应"),
        ReplCommand(".copy", "Copy last response", "复制上一个响应"),
        ReplCommand(".set", "Modify runtime settings", "修改运行时设置"),
        ReplCommand(".language", "Switch language (zh/en/auto)", "切换语言 (zh/en/auto)"),
        ReplCommand(".delete", "Delete roles, sessions, or RAGs", "删除角色、会话或 RAG"),
        ReplCommand(".exit", "Exit REPL", "退出 REPL"),
    ]

    def __init__(
        self,
        config: Any,
        history_file: Optional[str] = None,
    ):
        """Initialize the REPL.

        Args:
            config: Global configuration object
            history_file: Optional path to command history file
        """
        self.config = config
        self.history_file = history_file
        self.state = StateFlags(0)
        self.running = True

        # Store last response for .copy and .regenerate
        self.last_response: Optional[str] = None
        self.last_user_input: Optional[str] = None

        # Edit mode state
        self.edit_mode: Optional[str] = None  # 'role', 'session', 'rag'
        self.pending_input: Optional[str] = None

        # Continue mode
        self.continuing: bool = False

    def _get_prompt(self):
        """Get the current prompt string.

        Returns:
            Prompt string or HTML object for styled output
        """
        parts = []
        if StateFlags.AGENT in self.state:
            if hasattr(self.config, "agent") and self.config.agent:
                agent_name = getattr(self.config.agent, "name", "agent")
                parts.append(agent_name)

        if StateFlags.RAG in self.state:
            if hasattr(self.config, "rag") and self.config.rag:
                rag_name = self.config.rag.name
                parts.append(f"[{rag_name}]")

        if StateFlags.ROLE in self.state:
            if hasattr(self.config, "role") and self.config.role:
                role_name = getattr(self.config.role, "name", "")
                if role_name:
                    parts.append(f"@{role_name}")

        if parts:
            base = " ".join(parts)
            if PROMPT_TOOLKIT_AVAILABLE:
                return HTML(f'<style bg="ansigray" fg="ansicyan">{base}</style> <style fg="ansiyellow">></style> ')
            else:
                return f"{base}> "
        else:
            if PROMPT_TOOLKIT_AVAILABLE:
                return HTML('<style fg="ansiyellow">></style> ')
            else:
                return "> "

    def _get_session(self) -> Optional["PromptSession"]:
        """Get or create prompt session.

        Returns:
            PromptSession or None if prompt_toolkit unavailable
        """
        if not PROMPT_TOOLKIT_AVAILABLE:
            return None

        completer = WordCompleter([cmd.name for cmd in self.COMMANDS])
        key_bindings = KeyBindings()

        @key_bindings.add("c-c")
        def _(event):
            """Handle Ctrl+C - show help message."""
            event.app.exit(exception=KeyboardInterrupt)

        history = FileHistory(self.history_file) if self.history_file else None

        return PromptSession(
            completer=completer,
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=key_bindings,
        )

    async def run(self) -> None:
        """Run the REPL loop.

        This is the main entry point for the REPL.
        """
        if _is_chinese():
            print("欢迎使用 AICortex")
            print('输入 ".help" 查看可用命令')
        else:
            print("Welcome to AICortex")
            print('Type ".help" for available commands')
        print()

        session = self._get_session()

        while self.running:
            try:
                if session:
                    line = await session.prompt_async(self._get_prompt())
                else:
                    line = input(self._get_prompt())

                line = line.rstrip()

                if not line:
                    continue

                await self._handle_input(line)

            except KeyboardInterrupt:
                print("\n(To exit, press Ctrl+D or type '.exit')")
                continue
            except EOFError:
                break
            except Exception as e:
                print(f"\x1b[31mError: {e}\x1b[0m")
                continue

        print("\nGoodbye!")

    async def _handle_input(self, line: str) -> None:
        """Handle user input.

        Args:
            line: Input line
        """
        # Check for multiline input
        multiline_match = re.match(r"^\s*:::\s*(.*?)\s*:::\s*$", line, re.DOTALL)
        if multiline_match:
            line = multiline_match.group(1)

        # Parse command
        cmd, args = self._parse_command(line)

        if cmd:
            await self._run_command(cmd, args)
        else:
            # Regular input - send to LLM
            await self._send_to_llm(line)

    def _parse_command(self, line: str) -> tuple[Optional[str], Optional[str]]:
        """Parse a command from input.

        Supports both simple commands (.help) and compound commands (.edit role).

        Args:
            line: Input line

        Returns:
            Tuple of (command, args)
        """
        match = re.match(r"^\s*(\.\S*(?:\s+\S+)?)\s*(.*)$", line)
        if match:
            # Check for compound command (e.g., ".edit role")
            full_cmd = match.group(1).strip()
            remaining = match.group(2).strip() or None

            # Check if full_cmd is a compound command (space in it)
            if " " in full_cmd:
                parts = full_cmd.split(maxsplit=1)
                cmd = parts[0]
                # Combine the second part with remaining args
                sub_cmd = parts[1]
                args = f"{sub_cmd} {remaining}" if remaining else sub_cmd
                return cmd, args.strip() or None
            else:
                return full_cmd, remaining
        return None, None

    async def _run_command(self, cmd: str, args: Optional[str]) -> None:
        """Run a REPL command.

        Args:
            cmd: Command name
            args: Command arguments
        """
        match cmd:
            case ".help":
                self._dump_help()
            case ".exit":
                await self._cmd_exit(args)
            case ".info":
                await self._cmd_info(args)
            case ".model":
                await self._cmd_model(args)
            case ".role":
                await self._cmd_role(args)
            case ".session":
                await self._cmd_session(args)
            case ".rag":
                await self._cmd_rag(args)
            case ".set":
                await self._cmd_set(args)
            case ".copy":
                await self._cmd_copy(args)
            case ".continue":
                await self._cmd_continue(args)
            case ".regenerate":
                await self._cmd_regenerate(args)
            case ".file":
                await self._cmd_file(args)
            case ".edit":
                await self._cmd_edit(args)
            case ".save":
                await self._cmd_save(args)
            case ".rebuild":
                await self._cmd_rebuild(args)
            case ".sources":
                await self._cmd_sources(args)
            case ".empty":
                await self._cmd_empty(args)
            case ".compress":
                await self._cmd_compress(args)
            case ".agent":
                await self._cmd_agent(args)
            case ".starter":
                await self._cmd_starter(args)
            case ".macro":
                await self._cmd_macro(args)
            case ".language":
                await self._cmd_language(args)
            case _:
                print(_msg(f"未知命令: {cmd}", f"Unknown command: {cmd}"))
                print(_msg('输入 ".help" 查看可用命令', 'Type ".help" for available commands'))

    async def _cmd_info(self, args: Optional[str]) -> None:
        """Handle .info command.

        Args:
            args: Optional subcommand (role, session, rag, agent)
        """
        if args == "role":
            if hasattr(self.config, "role_info"):
                print(self.config.role_info())
            else:
                print(_msg("没有可用的角色信息", "No role info available"))
        elif args == "session":
            if hasattr(self.config, "session_info"):
                print(self.config.session_info())
            else:
                print(_msg("没有可用的会话信息", "No session info available"))
        elif args == "rag":
            if not (StateFlags.RAG in self.state and self.config.rag):
                print(_msg("没有活动的 RAG", "No active RAG"))
                return
            rag = self.config.rag
            info = rag.export()
            if _is_chinese():
                print(f"RAG: {rag.name}")
                print(f"路径: {info.get('path', 'N/A')}")
                print(f"嵌入模型: {info.get('embedding_model', 'N/A')}")
                print(f"重排序模型: {info.get('reranker_model', 'N/A')}")
                print(f"块大小: {info.get('chunk_size', 'N/A')}")
                print(f"块重叠: {info.get('chunk_overlap', 'N/A')}")
                print(f"Top K: {info.get('top_k', 'N/A')}")
                print(f"文件数: {len(info.get('files', []))}")
                print(f"文档数: {sum(f.get('num_chunks', 0) for f in info.get('files', []))}")
            else:
                print(f"RAG: {rag.name}")
                print(f"Path: {info.get('path', 'N/A')}")
                print(f"Embedding Model: {info.get('embedding_model', 'N/A')}")
                print(f"Reranker Model: {info.get('reranker_model', 'N/A')}")
                print(f"Chunk Size: {info.get('chunk_size', 'N/A')}")
                print(f"Chunk Overlap: {info.get('chunk_overlap', 'N/A')}")
                print(f"Top K: {info.get('top_k', 'N/A')}")
                print(f"Files: {len(info.get('files', []))}")
                print(f"Documents: {sum(f.get('num_chunks', 0) for f in info.get('files', []))}")
        elif args == "agent":
            if not (StateFlags.AGENT in self.state and self.config.agent):
                print(_msg("没有活动的 Agent", "No active agent"))
                return
            agent = self.config.agent
            print(_msg(f"Agent: {agent.name}", f"Agent: {agent.name}"))
            print(_msg(f"描述: {agent.definition.description}", f"Description: {agent.definition.description}"))
            print(_msg(f"版本: {agent.definition.version}", f"Version: {agent.definition.version}"))
            if agent.definition.variables:
                print(_msg("\n变量:", "\nVariables:"))
                for var in agent.definition.variables:
                    value = agent.variables().get(var.name, "<not set>")
                    print(f"  {var.name}: {value}")
                    if var.description:
                        print(f"    ({var.description})")
            if agent.definition.conversation_starters:
                print(_msg("\n对话开始语:", "\nConversation Starters:"))
                for starter in agent.definition.conversation_starters:
                    print(f"  - {starter}")
        else:
            # Show system info
            print(_msg("AICortex Python REPL", "AICortex Python REPL"))
            print(f"Python {sys.version}")

    async def _cmd_model(self, args: Optional[str]) -> None:
        """Handle .model command.

        Args:
            args: Model name or None
        """
        if not args:
            print(_msg("用法: .model <名称>", "Usage: .model <name>"))
            return

        if hasattr(self.config, "set_model"):
            self.config.set_model(args)
            print(_msg(f"模型已设置为: {args}", f"Model set to: {args}"))
        else:
            print(_msg("模型设置不可用", "Model setting not available"))

    async def _cmd_role(self, args: Optional[str]) -> None:
        """Handle .role command.

        Args:
            args: Role name or None
        """
        if not args:
            print(_msg("用法: .role <名称>", "Usage: .role <name>"))
            return

        if hasattr(self.config, "use_role"):
            self.config.use_role(args)
            self.state |= StateFlags.ROLE
            print(_msg(f"角色已设置为: {args}", f"Role set to: {args}"))
        else:
            print(_msg("角色设置不可用", "Role setting not available"))

    async def _cmd_session(self, args: Optional[str]) -> None:
        """Handle .session command.

        Args:
            args: Session name or None
        """
        if not args:
            print(_msg("用法: .session <名称>", "Usage: .session <name>"))
            return

        if hasattr(self.config, "use_session"):
            self.config.use_session(args)
            self.state |= StateFlags.SESSION
            print(_msg(f"会话已设置为: {args}", f"Session set to: {args}"))
        else:
            print(_msg("会话设置不可用", "Session setting not available"))

    async def _cmd_rag(self, args: Optional[str]) -> None:
        """Handle .rag command.

        Args:
            args: RAG name or None
        """
        if not args:
            print(_msg("用法: .rag <名称>", "Usage: .rag <name>"))
            return

        if hasattr(self.config, "use_rag"):
            self.config.use_rag(args)
            self.state |= StateFlags.RAG
            print(_msg(f"RAG 已设置为: {args}", f"RAG set to: {args}"))
        else:
            print(_msg("RAG 设置不可用", "RAG setting not available"))

    async def _cmd_set(self, args: Optional[str]) -> None:
        """Handle .set command.

        Args:
            args: Setting key=value or None
        """
        if not args:
            print(_msg("用法: .set <键>=<值>", "Usage: .set <key>=<value>"))
            return

        if "=" not in args:
            print(_msg("用法: .set <键>=<值>", "Usage: .set <key>=<value>"))
            return

        key, value = args.split("=", 1)
        key = key.strip()
        value = value.strip()

        if hasattr(self.config, "set_option"):
            self.config.set_option(key, value)
            print(_msg(f"已设置 {key} = {value}", f"Set {key} = {value}"))
        else:
            print(_msg(f"设置 '{key}' 不可用", f"Setting '{key}' not available"))

    async def _send_to_llm(self, text: str) -> None:
        """Send input to LLM.

        Args:
            text: User input
        """
        try:
            from ..llm import create_client, run_chat_completion
            from ..client import Message, MessageRole
            import os

            # Store user input for .continue and .regenerate
            self.last_user_input = text

            # Get current model
            model = self.config.current_model()

            # Get API key from environment or config
            api_key = os.environ.get("API_KEY") or os.environ.get(
                f"{model.client_name.upper()}_API_KEY", ""
            )

            # If not in environment, check config file
            if not api_key:
                client_config = self.config.get_client_config(model.client_name)
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
                print(f"\x1b[33m{_msg(f'警告: 未找到 {model.client_name} 的 API key', f'Warning: API key not found for {model.client_name}')}\x1b[0m")
                print(_msg(f"请设置 {model.client_name.upper()}_API_KEY 环境变量", f"Please set {model.client_name.upper()}_API_KEY environment variable"))
                print(_msg(f"或在 config.yaml 中添加 api_key 到 {model.client_name} 客户端", f"Or add api_key to the {model.client_name} client in config.yaml"))
                return

            # Create client
            client = await create_client(
                client_type=model.client_name,
                api_key=api_key,
                model=model,
            )

            # Get message history from session if available
            messages = []
            if hasattr(self.config, "session") and self.config.session:
                messages = self.config.session.messages

            # RAG search if enabled
            user_text = text
            if StateFlags.RAG in self.state and hasattr(self.config, "rag") and self.config.rag:
                try:
                    rag_context, doc_ids = await self.config.rag.search(text, config=self.config)
                    if rag_context:
                        # Add RAG context as system message
                        messages.append(Message.new(
                            MessageRole.SYSTEM,
                            f"参考以下文档内容回答问题：\n\n{rag_context}"
                        ))
                        # Store sources for .sources command
                        self.config.rag.set_last_sources(doc_ids)
                except Exception as e:
                    print(f"\x1b[33mRAG 搜索失败: {e}\x1b[0m")

            # Add current user message
            messages.append(Message.new(MessageRole.USER, user_text))

            # Run chat completion
            print()  # Empty line before response
            response = await run_chat_completion(
                client=client,
                messages=messages,
                stream=self.config.stream,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
            )

            # Store response for .copy and .regenerate
            self.last_response = response

            # Update session
            if hasattr(self.config, "session") and self.config.session:
                if hasattr(self.config.session, "add_message"):
                    self.config.session.add_message(Message.new(MessageRole.USER, text))
                    self.config.session.add_message(Message.new(MessageRole.ASSISTANT, response))

            # Close client
            await client.close()

        except Exception as e:
            print(f"\x1b[31mError: {e}\x1b[0m")

    def _dump_help(self) -> None:
        """Print help information."""
        if _is_chinese():
            print("可用命令:")
        else:
            print("Available commands:")
        print()

        # Group commands by category (localized)
        if _is_chinese():
            categories = {
                "基本": [".help", ".info", ".model", ".set", ".exit"],
                "角色": [
                    ".prompt",
                    ".role",
                    ".info role",
                    ".edit role",
                    ".save role",
                    ".exit role",
                ],
                "会话": [
                    ".session",
                    ".empty session",
                    ".compress session",
                    ".info session",
                    ".edit session",
                    ".save session",
                    ".exit session",
                ],
                "RAG": [
                    ".rag",
                    ".edit rag-docs",
                    ".rebuild rag",
                    ".sources rag",
                    ".info rag",
                    ".exit rag",
                ],
                "输入": [".file", ".continue", ".regenerate", ".copy"],
                "管理": [".delete"],
            }
        else:
            categories = {
                "General": [".help", ".info", ".model", ".set", ".exit"],
                "Role": [
                    ".prompt",
                    ".role",
                    ".info role",
                    ".edit role",
                    ".save role",
                    ".exit role",
                ],
                "Session": [
                    ".session",
                    ".empty session",
                    ".compress session",
                    ".info session",
                    ".edit session",
                    ".save session",
                    ".exit session",
                ],
                "RAG": [
                    ".rag",
                    ".edit rag-docs",
                    ".rebuild rag",
                    ".sources rag",
                    ".info rag",
                    ".exit rag",
                ],
                "Input": [".file", ".continue", ".regenerate", ".copy"],
                "Management": [".delete"],
            }

        for category, commands in categories.items():
            print(f"\x1b[1;33m{category}\x1b[0m")
            for cmd_name in commands:
                for cmd in self.COMMANDS:
                    if cmd.name == cmd_name:
                        if cmd.is_valid(self.state):
                            print(f"  {cmd.name:<20} {cmd.get_description()}")
                        else:
                            print(f"  \x1b[90m{cmd.name:<20} {cmd.get_description()}\x1b[0m")
                        break
            print()

    async def _cmd_exit(self, args: Optional[str]) -> None:
        """Handle .exit command.

        Args:
            args: Optional subcommand (role, session, rag, agent)
        """
        if not args:
            # Exit REPL
            self.running = False
            return

        # Handle subcommands: .exit role, .exit session, .exit rag, .exit agent
        match args.split():
            case ["role"]:
                if StateFlags.ROLE in self.state:
                    self.state &= ~StateFlags.ROLE
                    self.config.role = None
                    print(_msg("已退出角色模式", "Exited role mode"))
                else:
                    print(_msg("未在角色模式中", "Not in role mode"))
            case ["session"]:
                if StateFlags.SESSION in self.state:
                    self.state &= ~StateFlags.SESSION
                    self.config.session = None
                    print(_msg("已退出会话模式", "Exited session mode"))
                else:
                    print(_msg("未在会话模式中", "Not in session mode"))
            case ["rag"]:
                if StateFlags.RAG in self.state:
                    self.state &= ~StateFlags.RAG
                    self.config.rag = None
                    print(_msg("已退出 RAG 模式", "Exited RAG mode"))
                else:
                    print(_msg("未在 RAG 模式中", "Not in RAG mode"))
            case ["agent"]:
                if StateFlags.AGENT in self.state:
                    self.state &= ~StateFlags.AGENT
                    self.config.agent = None
                    print(_msg("已退出 Agent 模式", "Exited agent mode"))
                else:
                    print(_msg("未在 Agent 模式中", "Not in agent mode"))
            case _:
                print(_msg(f"未知的退出子命令: {args}", f"Unknown exit subcommand: {args}"))

    async def _cmd_copy(self, args: Optional[str]) -> None:
        """Handle .copy command.

        Args:
            args: Optional text to copy (defaults to last response)
        """
        from ..utils.clipboard import copy, ClipboardError

        text_to_copy = args if args else self.last_response

        if not text_to_copy:
            print(_msg("没有可复制的内容", "No content to copy"))
            return

        try:
            copy(text_to_copy)
            print(_msg("已复制到剪贴板", "Copied to clipboard"))
        except ClipboardError as e:
            print(_msg(f"复制失败: {e}", f"Failed to copy: {e}"))

    async def _cmd_language(self, args: Optional[str]) -> None:
        """Handle .language command.

        Usage:
            .language           - Show current language setting
            .language zh        - Switch to Chinese
            .language en        - Switch to English
            .language auto      - Use system language detection

        Args:
            args: Language option (zh, en, auto) or None to show current
        """
        if not args:
            # Show current language setting
            current = _LANGUAGE_SETTING or 'auto'
            print(_msg(f"当前语言: {current}", f"Current language: {current}"))
            print(_msg("用法: .language [zh|en|auto]", "Usage: .language [zh|en|auto]"))
            return

        # Set language
        try:
            set_language(args)
            print(_msg(f"语言已设置为: {args}", f"Language set to: {args}"))
        except ValueError as e:
            print(_msg(f"错误: {e}", f"Error: {e}"))
            print(_msg("用法: .language [zh|en|auto]", "Usage: .language [zh|en|auto]"))

    async def _cmd_continue(self, args: Optional[str]) -> None:
        """Handle .continue command.

        Continues generating from the last response.
        """
        if not self.last_response:
            print(_msg("没有可继续的响应", "No previous response to continue"))
            return

        # Create continuation prompt
        continue_prompt = self.last_user_input or _msg("请继续", "Please continue")

        # Set continuing flag
        self.continuing = True

        # Send to LLM
        await self._send_to_llm(continue_prompt)

        self.continuing = False

    async def _cmd_regenerate(self, args: Optional[str]) -> None:
        """Handle .regenerate command.

        Regenerates the last response.
        """
        if not self.last_user_input:
            print(_msg("没有可重新生成的消息", "No previous message to regenerate"))
            return

        # Remove last messages from session if exists
        if hasattr(self.config, "session") and self.config.session:
            if hasattr(self.config.session, "messages"):
                messages = self.config.session.messages
                # Remove last assistant message (and user message if continuing)
                if len(messages) >= 2:
                    messages.pop()  # Remove assistant
                    messages.pop()  # Remove user

        # Resend the last user input
        await self._send_to_llm(self.last_user_input)

    async def _cmd_file(self, args: Optional[str]) -> None:
        """Handle .file command.

        Args:
            args: File path or None to show usage
        """
        import os

        if not args:
            print(_msg("用法: .file <路径>", "Usage: .file <path>"))
            print(_msg("在消息中包含文件内容", "Include file contents in your message"))
            return

        path = args.strip()
        if not os.path.exists(path):
            print(_msg(f"文件未找到: {path}", f"File not found: {path}"))
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"--- {path} ---")
            print(content)
            print(f"--- End of {path} ---")
            print(_msg("\n您现在可以在消息中引用此文件。", "\nYou can now reference this file in your message."))

            # Store for next message
            self.pending_input = f"[File: {path}]\n{content}"

        except Exception as e:
            print(_msg(f"读取文件错误: {e}", f"Error reading file: {e}"))

    async def _cmd_edit(self, args: Optional[str]) -> None:
        """Handle .edit command.

        Args:
            args: Subcommand (role, session, rag-docs, config, agent)
        """
        if not args:
            print(_msg("用法: .edit <目标>", "Usage: .edit <target>"))
            print(_msg("目标: role, session, rag-docs, config, agent-config", "Targets: role, session, rag-docs, config, agent-config"))
            return

        # Handle rag-docs as a single token
        if args.startswith("rag-docs"):
            await self._cmd_edit_rag_docs(args)
            return

        # Handle agent-config as a single token
        if args == "agent-config":
            await self._cmd_edit_agent_config()
            return

        match args.split():
            case ["role"]:
                if not (StateFlags.ROLE in self.state and self.config.role):
                    print(_msg("没有活动的角色可编辑", "No active role to edit"))
                    return
                print(_msg("进入角色编辑模式", "Enter role editing mode"))
                print(_msg("输入新的角色内容 (完成后按 Ctrl+D):", "Enter new role content (press Ctrl+D when done):"))
                try:
                    lines = []
                    while True:
                        try:
                            line = input("... ")
                        except EOFError:
                            break
                        lines.append(line)
                    content = "\n".join(lines)
                    # Update role
                    if hasattr(self.config.role, "update_text"):
                        self.config.role.update_text(content)
                    print(_msg("角色已更新", "Role updated"))
                except KeyboardInterrupt:
                    print(_msg("\n编辑已取消", "\nEdit cancelled"))

            case ["session"]:
                if not (StateFlags.SESSION in self.state and self.config.session):
                    print(_msg("没有活动的会话可编辑", "No active session to edit"))
                    return
                print(_msg("进入会话编辑模式", "Enter session editing mode"))
                print(_msg("输入新的会话内容 (完成后按 Ctrl+D):", "Enter new session content (press Ctrl+D when done):"))
                try:
                    lines = []
                    while True:
                        try:
                            line = input("... ")
                        except EOFError:
                            break
                        lines.append(line)
                    content = "\n".join(lines)
                    # Update session
                    if hasattr(self.config.session, "update_messages"):
                        self.config.session.update_messages(content)
                    print(_msg("会话已更新", "Session updated"))
                except KeyboardInterrupt:
                    print(_msg("\n编辑已取消", "\nEdit cancelled"))

            case ["config"]:
                print(_msg("配置文件编辑尚未实现", "Config file editing not yet implemented"))
                print(_msg("您可以手动编辑: ~/.config/aicortex/config.yaml", "You can manually edit: ~/.config/aicortex/config.yaml"))

            case ["agent"]:
                print(_msg("使用 '.edit agent-config' 编辑 Agent 配置", "Use '.edit agent-config' to edit agent configuration"))

            case _:
                print(_msg(f"未知的编辑目标: {args}", f"Unknown edit target: {args}"))

    async def _cmd_edit_rag_docs(self, args: str) -> None:
        """Handle .edit rag-docs command.

        Args:
            args: Full arguments (e.g., "rag-docs", "rag-docs --add", "rag-docs --remove")
        """
        if not (StateFlags.RAG in self.state and self.config.rag):
            print(_msg("没有活动的 RAG 可编辑", "No active RAG to edit"))
            return

        rag = self.config.rag

        # Parse arguments
        parts = args.split()
        action = None
        paths = []

        i = 0
        while i < len(parts):
            if parts[i] == "rag-docs":
                i += 1
            elif parts[i] in ["--add", "-a", "--remove", "-r", "--list", "-l"]:
                action = parts[i]
                i += 1
            else:
                # Treat as file path
                paths.append(parts[i])
                i += 1

        if action == "--list" or action == "-l":
            # List documents in RAG
            print(_msg(f"RAG '{rag.name}' 中的文档:", f"Documents in RAG '{rag.name}':"))

            # Show indexed files
            for file_id, file in rag.data.files.items():
                print(f"  [{file_id}] {file.path} ({len(file.documents)} chunks)")

            # Show pending documents (not yet indexed)
            pending = [p for p in rag.data.document_paths if not any(f.path == p for f in rag.data.files.values())]
            if pending:
                print(_msg("\n待索引文档:", "\nPending documents (not indexed):"))
                for p in pending:
                    print(f"  - {p}")

            if not rag.data.files and not rag.data.document_paths:
                print(_msg("  (没有文档)", "  (No documents)"))

        elif action == "--add" or action == "-a":
            # Add documents
            if not paths:
                print(_msg("用法: .edit rag-docs --add <路径1> <路径2> ...", "Usage: .edit rag-docs --add <path1> <path2> ..."))
                return

            import os
            added = 0
            for path_str in paths:
                path = Path(path_str)
                if not path.exists():
                    print(_msg(f"文件未找到: {path}", f"File not found: {path}"))
                    continue

                # Check if already indexed
                for existing_file in rag.data.files.values():
                    if existing_file.path == str(path):
                        print(_msg(f"已索引: {path}", f"Already indexed: {path}"))
                        continue

                # Read and index file
                try:
                    content = path.read_text(encoding="utf-8")
                    print(_msg(f"正在索引: {path}", f"Indexing: {path}"))

                    # TODO: This is a simplified version
                    # In production, you would:
                    # 1. Split the document
                    # 2. Generate embeddings
                    # 3. Update the RAG data
                    # 4. Rebuild indexes

                    # For now, just add to document_paths
                    rag.data.document_paths.append(str(path))
                    added += 1
                    print(_msg(f"  已添加: {path}", f"  Added: {path}"))

                except Exception as e:
                    print(_msg(f"索引 {path} 时出错: {e}", f"Error indexing {path}: {e}"))

            if added > 0:
                print(_msg(f"\n已添加 {added} 个文件", f"\nAdded {added} file(s)"))
                print(_msg("注意: 搜索需要重建索引。使用: .rebuild rag", "Note: Index rebuild required for search. Use: .rebuild rag"))
                # Save RAG
                rag.save()

        elif action == "--remove" or action == "-r":
            # Remove documents
            if not paths:
                print(_msg("用法: .edit rag-docs --remove <文件ID> ...", "Usage: .edit rag-docs --remove <file_id> ..."))
                print(_msg("使用 .edit rag-docs --list 查看文件 ID", "Use .edit rag-docs --list to see file IDs"))
                return

            removed = 0
            for path_str in paths:
                # Try to parse as file ID
                try:
                    file_id = int(path_str)
                    if file_id in rag.data.files:
                        file_path = rag.data.files[file_id].path
                        rag.data.del_files([file_id])
                        rag.data.document_paths = [
                            p for p in rag.data.document_paths
                            if p != file_path
                        ]
                        print(_msg(f"已移除: [{file_id}] {file_path}", f"Removed: [{file_id}] {file_path}"))
                        removed += 1
                    else:
                        print(_msg(f"文件 ID 未找到: {file_id}", f"File ID not found: {file_id}"))
                except ValueError:
                    print(_msg(f"无效的文件 ID: {path_str}", f"Invalid file ID: {path_str}"))

            if removed > 0:
                print(_msg(f"\n已移除 {removed} 个文件", f"\nRemoved {removed} file(s)"))
                print(_msg("注意: 需要重建索引。使用: .rebuild rag", "Note: Index rebuild required. Use: .rebuild rag"))

        else:
            # No action specified, show help
            print(_msg("RAG 文档编辑", "RAG Document Editing"))
            print()
            print(_msg("用法:", "Usage:"))
            print("  .edit rag-docs --list")
            print(_msg("  .edit rag-docs --add <路径1> <路径2> ...", "  .edit rag-docs --add <path1> <path2> ..."))
            print(_msg("  .edit rag-docs --remove <文件ID> ...", "  .edit rag-docs --remove <file_id> ..."))
            print()
            print(_msg("操作:", "Actions:"))
            print(_msg("  --list, -l       列出所有文档", "  --list, -l       List all documents"))
            print(_msg("  --add, -a       添加文档到 RAG", "  --add, -a       Add documents to RAG"))
            print(_msg("  --remove, -r    从 RAG 移除文档", "  --remove, -r    Remove documents from RAG"))
            print()
            print(_msg("添加/移除后，运行: .rebuild rag", "After adding/removing, run: .rebuild rag"))

    async def _cmd_save(self, args: Optional[str]) -> None:
        """Handle .save command.

        Args:
            args: Subcommand (role, session) or None
        """
        if not args:
            print(_msg("用法: .save <目标>", "Usage: .save <target>"))
            print(_msg("目标: role, session", "Targets: role, session"))
            return

        match args.split():
            case ["role"]:
                if not (StateFlags.ROLE in self.state and self.config.role):
                    print(_msg("没有活动的角色可保存", "No active role to save"))
                    return

                role_name = getattr(self.config.role, "name", "custom")
                role_path = self.config._get_config_path().parent / "roles" / f"{role_name}.md"

                try:
                    role_path.parent.mkdir(parents=True, exist_ok=True)
                    role_content = self.config.role.save_text()
                    role_path.write_text(role_content, encoding="utf-8")
                    print(_msg(f"角色已保存到: {role_path}", f"Role saved to: {role_path}"))
                except Exception as e:
                    print(_msg(f"保存角色失败: {e}", f"Failed to save role: {e}"))

            case ["session"]:
                if not (StateFlags.SESSION in self.state and self.config.session):
                    print(_msg("没有活动的会话可保存", "No active session to save"))
                    return

                session_name = getattr(self.config.session, "name", "chat")
                session_path = self.config._get_config_path().parent / "sessions" / f"{session_name}.yaml"

                try:
                    session_path.parent.mkdir(parents=True, exist_ok=True)
                    if hasattr(self.config.session, "save"):
                        self.config.session.save(session_path)
                    print(_msg(f"会话已保存到: {session_path}", f"Session saved to: {session_path}"))
                except Exception as e:
                    print(_msg(f"保存会话失败: {e}", f"Failed to save session: {e}"))

            case _:
                print(_msg(f"未知的保存目标: {args}", f"Unknown save target: {args}"))

    async def _cmd_rebuild(self, args: Optional[str]) -> None:
        """Handle .rebuild rag command.

        Rebuilds RAG indexes after document changes.

        Args:
            args: Should be "rag"
        """
        if args != "rag":
            print(_msg("用法: .rebuild rag", "Usage: .rebuild rag"))
            return

        if not (StateFlags.RAG in self.state and self.config.rag):
            print(_msg("没有活动的 RAG 可重建", "No active RAG to rebuild"))
            return

        rag = self.config.rag

        # Check if RAG is temporary (cannot be saved)
        if rag.is_temp():
            print(_msg("无法重建临时 RAG", "Cannot rebuild temporary RAG"))
            return

        print(_msg(f"正在重建 RAG '{rag.name}'...", f"Rebuilding RAG '{rag.name}'..."))

        try:
            # Process pending documents and generate embeddings
            pending = [p for p in rag.data.document_paths if not any(f.path == p for f in rag.data.files.values())]
            if pending:
                print(_msg(f"处理 {len(pending)} 个待处理文档...", f"Processing {len(pending)} pending document(s)..."))
                processed = await rag.build_from_paths(self.config)
                print(_msg(f"已处理 {processed} 个文档", f"Processed {processed} document(s)"))
            else:
                # Just rebuild indexes from existing data
                rag._build_indexes()

            # Save RAG data
            rag.save()

            print(_msg("RAG 重建成功", "RAG rebuilt successfully"))

            # Show summary
            num_files = len(rag.data.files)
            num_docs = sum(len(f.documents) for f in rag.data.files.values())
            num_vectors = len(rag.data.vectors)

            print(f"  Files: {num_files}")
            print(f"  Documents: {num_docs}")
            print(f"  Vectors: {num_vectors}")

        except Exception as e:
            print(_msg(f"重建 RAG 错误: {e}", f"Error rebuilding RAG: {e}"))

    async def _cmd_sources(self, args: Optional[str]) -> None:
        """Handle .sources rag command.

        Shows citation sources used in the last query.

        Args:
            args: Should be "rag"
        """
        if args != "rag":
            print(_msg("用法: .sources rag", "Usage: .sources rag"))
            return

        if not (StateFlags.RAG in self.state and self.config.rag):
            print(_msg("没有活动的 RAG", "No active RAG"))
            return

        rag = self.config.rag
        sources = rag.get_last_sources()

        if not sources:
            print(_msg("没有可用的来源 (请先运行查询)", "No sources available (run a query first)"))
            return

        print(_msg("来源:", "Sources:"))
        print(sources)

    async def _cmd_empty(self, args: Optional[str]) -> None:
        """Handle .empty session command.

        Clears all messages from the current session.

        Args:
            args: Should be "session"
        """
        if args != "session":
            print(_msg("用法: .empty session", "Usage: .empty session"))
            return

        if not (StateFlags.SESSION in self.state and self.config.session):
            print(_msg("没有活动的会话可清空", "No active session to empty"))
            return

        session = self.config.session

        # Check if session has messages
        if session.is_empty():
            print(_msg("会话已经是空的", "Session is already empty"))
            return

        # Confirm before clearing
        print(_msg(f"清空会话 '{session.name}' 中的所有消息?", f"Clear all messages from session '{session.name}'?"))
        try:
            confirm = input(_msg("确认 (y/N): ", "Confirm (y/N): ")).strip().lower()
            if confirm != "y":
                print(_msg("已取消", "Cancelled"))
                return
        except (KeyboardInterrupt, EOFError):
            print(_msg("\n已取消", "\nCancelled"))
            return

        # Clear messages
        session.clear_messages()
        print(_msg(f"会话 '{session.name}' 已清空", f"Session '{session.name}' cleared"))

    async def _cmd_compress(self, args: Optional[str]) -> None:
        """Handle .compress session command.

        Compresses session messages into a summary.

        Args:
            args: Should be "session"
        """
        if args != "session":
            print(_msg("用法: .compress session", "Usage: .compress session"))
            return

        if not (StateFlags.SESSION in self.state and self.config.session):
            print(_msg("没有活动的会话可压缩", "No active session to compress"))
            return

        session = self.config.session

        # Check if session has messages
        if session.is_empty():
            print(_msg("无法压缩空会话", "Cannot compress empty session"))
            return

        print(_msg(f"正在压缩会话 '{session.name}'...", f"Compressing session '{session.name}'..."))

        # Default compression prompt
        compress_prompt = """Please summarize the following conversation concisely:
- Focus on key information and decisions
- Omit redundant details
- Use bullet points for clarity
- Keep the summary under 500 words

Conversation:"""

        # Compress session
        try:
            session.compress(compress_prompt)
            print(_msg("会话压缩成功", "Session compressed successfully"))

            # Show summary
            num_messages = len(session.compressed_messages)
            tokens, percent = session.tokens_usage()
            print(_msg(f"  已压缩 {num_messages} 条消息", f"  Compressed {num_messages} messages"))
            print(f"  Current tokens: {tokens} ({percent:.1f}%)")

        except Exception as e:
            print(_msg(f"压缩会话错误: {e}", f"Error compressing session: {e}"))

    async def _cmd_agent(self, args: Optional[str]) -> None:
        """Handle .agent command.

        Enter or switch to Agent mode.

        Args:
            args: Agent name
        """
        if not args:
            print(_msg("用法: .agent <名称>", "Usage: .agent <name>"))
            print(_msg("\n可用的 Agents:", "\nAvailable agents:"))
            # Try to list available agents
            agents_dir = Path("agents")
            if agents_dir.exists():
                for agent_dir in agents_dir.iterdir():
                    if agent_dir.is_dir() and (agent_dir / "index.yaml").exists():
                        print(f"  - {agent_dir.name}")
            return

        # Check if config supports agent
        if not hasattr(self.config, "use_agent"):
            print(_msg("Agent 模式不可用", "Agent mode not available"))
            return

        try:
            # Initialize agent
            from ..agent import Agent
            agent = await Agent.init(self.config, args)

            # Set as active agent
            self.config.agent = agent
            self.state |= StateFlags.AGENT

            # Show agent banner
            print(agent.banner())

            # Show conversation starters if available
            starters = agent.conversation_starters()
            if starters:
                print(_msg("\n提示: 使用 '.starter' 设置对话开始语", "\nTip: Use '.starter' to set a conversation starter"))

        except ValueError as e:
            print(_msg(f"错误: {e}", f"Error: {e}"))
        except Exception as e:
            print(_msg(f"加载 Agent 失败: {e}", f"Failed to load agent: {e}"))

    async def _cmd_edit_agent_config(self) -> None:
        """Handle .edit agent-config command.

        Edit the current agent's configuration.
        """
        if not (StateFlags.AGENT in self.state and self.config.agent):
            print(_msg("没有活动的 Agent 可编辑", "No active agent to edit"))
            return

        agent = self.config.agent

        print(_msg(f"正在编辑 Agent '{agent.name}' 配置", f"Editing agent '{agent.name}' configuration"))
        print(_msg("\n当前配置:", "\nCurrent configuration:"))
        print(f"  Model: {agent.config.model_id or '<default>'}")
        print(f"  Temperature: {agent.config.temperature or '<default>'}")
        print(f"  Top P: {agent.config.top_p or '<default>'}")
        print(f"  Use Tools: {agent.config.use_tools or '<default>'}")

        print(_msg("\n输入变量值 (完成后按 Ctrl+D):", "\nEnter variable values (press Ctrl+D when done):"))
        print(_msg("格式: variable_name=value", "Format: variable_name=value"))

        try:
            lines = []
            while True:
                try:
                    line = input("... ")
                except EOFError:
                    break
                if line.strip():
                    lines.append(line)

            # Parse variable assignments
            from collections import OrderedDict
            new_vars = OrderedDict()
            for line in lines:
                if "=" in line:
                    key, value = line.split("=", 1)
                    new_vars[key.strip()] = value.strip()

            # Update agent variables
            if new_vars:
                agent.set_session_variables(new_vars)
                print(_msg(f"\n已更新 {len(new_vars)} 个变量", f"\nUpdated {len(new_vars)} variable(s)"))

        except KeyboardInterrupt:
            print(_msg("\n编辑已取消", "\nEdit cancelled"))

    async def _cmd_starter(self, args: Optional[str]) -> None:
        """Handle .starter command.

        Set a conversation starter for the current agent.

        Args:
            args: Optional starter index or text
        """
        if not (StateFlags.AGENT in self.state and self.config.agent):
            print(_msg("没有活动的 Agent", "No active agent"))
            return

        agent = self.config.agent
        starters = agent.conversation_starters()

        if not starters:
            print(_msg("此 Agent 没有可用的对话开始语", "No conversation starters available for this agent"))
            return

        if not args:
            # List available starters
            print(_msg(f"'{agent.name}' 的对话开始语:", f"Conversation starters for '{agent.name}':"))
            for i, starter in enumerate(starters, 1):
                print(f"  {i}. {starter}")
            print(_msg("\n用法: .starter <数字> 或 .starter <文本>", "\nUsage: .starter <number> or .starter <text>"))
            return

        # Check if args is a number
        try:
            index = int(args) - 1
            if 0 <= index < len(starters):
                starter_text = starters[index]
                # Send the starter as input
                await self._handle_input(starter_text)
            else:
                print(_msg(f"无效的开始语编号 (1-{len(starters)})", f"Invalid starter number (1-{len(starters)})"))
        except ValueError:
            # Use args as direct text
            await self._handle_input(args)

    async def _cmd_macro(self, args: Optional[str]) -> None:
        """Handle .macro command.

        Execute a macro or list available macros.

        Args:
            args: Optional macro name and arguments
        """
        # Import here to avoid circular dependency
        from ..config.macro import Macro, MacroRegistry

        # Use macros directory from config if available
        macros_dir = getattr(self.config, "macros_dir", None) or Path("macros")
        registry = MacroRegistry(macros_dir)

        if not args:
            # List available macros
            macros = registry.list_macros()
            if not macros:
                print(_msg("没有可用的宏", "No macros available"))
                print(_msg("\n在 macros 目录中创建宏:", "\nCreate macros in the macros directory:"))
                print(f"  {macros_dir}/<name>.yaml")
                return

            print(_msg("可用的宏:", "Available macros:"))
            for macro_name in macros:
                try:
                    macro = registry.load_macro(macro_name)
                    usage = macro.usage(f".macro {macro_name}")
                    print(f"  {usage}")
                except Exception:
                    print(f"  {macro_name}")
            return

        # Parse macro name and arguments
        parts = args.split(None, 1)
        macro_name = parts[0]
        macro_args = parts[1].split() if len(parts) > 1 else []

        # Check if macro exists
        if not registry.has_macro(macro_name):
            print(_msg(f"未找到宏: {macro_name}", f"Macro not found: {macro_name}"))
            print(_msg("\n可用的宏:", "\nAvailable macros:"))
            for name in registry.list_macros():
                print(f"  - {name}")
            return

        # Load and execute macro
        try:
            macro = registry.load_macro(macro_name)

            # Resolve variables from arguments
            variables = macro.resolve_variables(macro_args)

            # Execute each step
            for step in macro.steps:
                # Interpolate variables into the command
                command = Macro.interpolate_command(step, variables)

                # Parse and execute the command
                if command.startswith("."):
                    # It's a REPL command
                    cmd_parts = command.split(None, 1)
                    cmd_name = cmd_parts[0]
                    cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else None
                    await self._run_command(cmd_name, cmd_args)
                else:
                    # It's regular input - send to LLM
                    await self._handle_input(command)

        except ValueError as e:
            print(_msg(f"错误: {e}", f"Error: {e}"))
            print(_msg(f"\n用法: {macro.usage(f'.macro {macro_name}')}", f"\nUsage: {macro.usage(f'.macro {macro_name}')}"))
        except Exception as e:
            print(_msg(f"执行宏错误: {e}", f"Error executing macro: {e}"))


__all__ = ["Repl", "ReplCommand", "StateFlags"]
