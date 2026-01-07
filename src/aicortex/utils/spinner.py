"""Loading spinner utilities.

Corresponds to src/utils/spinner.rs in the Rust implementation.
"""

import sys
import asyncio
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class SpinnerEvent(Enum):
    """Spinner control events."""

    SET_MESSAGE = "set_message"
    STOP = "stop"


@dataclass
class SpinnerInner:
    """Internal spinner state.

    Attributes:
        index: Current frame index
        message: Current message to display
        frames: Animation frames
    """

    index: int = 0
    message: str = ""
    frames: list[str] = None

    def __post_init__(self) -> None:
        if self.frames is None:
            self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def step(self) -> str:
        """Advance to next frame and return render string.

        Returns:
            Rendered spinner line
        """
        if not self.message:
            return ""

        frame = self.frames[self.index % len(self.frames)]
        dots = ".".repeat((self.index // 5) % 4)
        line = f"{frame} {self.message}{dots:<3}"
        self.index += 1
        return line

    def set_message(self, message: str) -> None:
        """Set the spinner message.

        Args:
            message: New message to display
        """
        self.message = message

    def clear(self) -> str:
        """Get clear sequence.

        Returns:
            String to clear the spinner line
        """
        if not self.message:
            return ""
        return "\r" + " " * 80 + "\r"


class Spinner:
    """Async loading spinner with message updates.

    Example:
        async def long_task():
            spinner = Spinner.create("Loading...")
            try:
                await asyncio.sleep(2)
                spinner.set_message("Almost done...")
                await asyncio.sleep(1)
            finally:
                spinner.stop()
    """

    def __init__(self) -> None:
        """Initialize the spinner."""
        self._stop_event = threading.Event()
        self._message_event = threading.Event()
        self._message: str = ""
        self._task: Optional[asyncio.Task] = None
        self._inner = SpinnerInner()

    @classmethod
    def create(cls, message: str) -> "Spinner":
        """Create and start a spinner.

        Args:
            message: Initial message to display

        Returns:
            Started Spinner instance
        """
        spinner = cls()
        spinner._inner.set_message(message)
        spinner._start()
        return spinner

    def set_message(self, message: str) -> None:
        """Update the spinner message.

        Args:
            message: New message to display
        """
        self._message = message
        self._message_event.set()
        # Small delay to ensure the message is processed
        import time
        time.sleep(0.01)

    def stop(self) -> None:
        """Stop the spinner and clear the line."""
        self._stop_event.set()
        if self._task:
            self._task.join(timeout=1.0)
            self._task = None
        # Clear the spinner line
        sys.stdout.write(self._inner.clear())
        sys.stdout.flush()

    def _start(self) -> None:
        """Start the spinner thread."""
        self._task = threading.Thread(target=self._run, daemon=True)
        self._task.start()

    def _run(self) -> None:
        """Run the spinner animation loop."""
        import time

        while not self._stop_event.is_set():
            # Check for message update
            if self._message_event.is_set():
                self._inner.set_message(self._message)
                self._message_event.clear()

            # Render spinner
            line = self._inner.step()
            if line:
                sys.stdout.write(f"\r{line}")
                sys.stdout.flush()

            # Wait before next frame
            time.sleep(0.05)


class AsyncSpinner:
    """Async context manager for running tasks with a spinner.

    Example:
        async with AsyncSpinner("Loading...") as spinner:
            await long_operation()
            spinner.set_message("Processing...")
    """

    def __init__(self, message: str) -> None:
        """Initialize the async spinner.

        Args:
            message: Initial message
        """
        self.message = message
        self.spinner: Optional[Spinner] = None
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self) -> "AsyncSpinner":
        """Enter the context and start the spinner."""
        self.spinner = Spinner.create(self.message)
        return self

    async def __aexit__(self, *args) -> None:
        """Exit the context and stop the spinner."""
        if self.spinner:
            self.spinner.stop()

    def set_message(self, message: str) -> None:
        """Update the spinner message.

        Args:
            message: New message
        """
        if self.spinner:
            self.spinner.set_message(message)


def run_with_spinner(
    func: Callable,
    message: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Run a synchronous function with a spinner.

    Args:
        func: Function to run
        message: Spinner message
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Examples:
        >>> result = run_with_spinner(long_operation, "Processing...")
    """
    spinner = Spinner.create(message)

    try:
        result = func(*args, **kwargs)
        return result
    finally:
        spinner.stop()


async def run_async_with_spinner(
    coro: Callable,
    message: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Run an async function with a spinner.

    Args:
        coro: Async function to run
        message: Spinner message
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Coroutine result

    Examples:
        >>> result = await run_async_with_spinner(async_operation, "Loading...")
    """
    spinner = Spinner.create(message)

    try:
        result = await coro(*args, **kwargs)
        return result
    finally:
        spinner.stop()


def simple_spinner(message: str) -> Spinner:
    """Create a simple spinner (alias for Spinner.create).

    Args:
        message: Initial message

    Returns:
        Started Spinner instance

    Examples:
        >>> spinner = simple_spinner("Loading...")
        >>> # Do work...
        >>> spinner.stop()
    """
    return Spinner.create(message)


__all__ = [
    "SpinnerEvent",
    "SpinnerInner",
    "Spinner",
    "AsyncSpinner",
    "run_with_spinner",
    "run_async_with_spinner",
    "simple_spinner",
]
