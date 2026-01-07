"""Main entry point for AIChat.

Corresponds to src/main.rs in the Rust implementation.
"""

import asyncio
import sys
from typing import Optional
import typer
from pathlib import Path

from .cli import app


if __name__ == "__main__":
    app()
