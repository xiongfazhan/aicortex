"""Abort signal handling for async operations.

Corresponds to src/utils/abort_signal.rs in the Rust implementation.
"""

import asyncio
import threading
from typing import Optional


class AbortSignal:
    """Signal for aborting async operations.

    Provides thread-safe signaling for Ctrl+C and Ctrl+D interrupts.

    Attributes:
        _ctrlc: Event for Ctrl+C signal
        _ctrld: Event for Ctrl+D signal
    """

    def __init__(self) -> None:
        """Create a new abort signal."""
        self._ctrlc = threading.Event()
        self._ctrld = threading.Event()

    def aborted(self) -> bool:
        """Check if the operation should be aborted.

        Returns:
            True if either Ctrl+C or Ctrl+D was triggered
        """
        return self._ctrlc.is_set() or self._ctrld.is_set()

    def aborted_ctrlc(self) -> bool:
        """Check if Ctrl+C was triggered.

        Returns:
            True if Ctrl+C was triggered
        """
        return self._ctrlc.is_set()

    def aborted_ctrld(self) -> bool:
        """Check if Ctrl+D was triggered.

        Returns:
            True if Ctrl+D was triggered
        """
        return self._ctrld.is_set()

    def reset(self) -> None:
        """Reset the abort signal."""
        self._ctrlc.clear()
        self._ctrld.clear()

    def set_ctrlc(self) -> None:
        """Set the Ctrl+C abort signal."""
        self._ctrlc.set()

    def set_ctrld(self) -> None:
        """Set the Ctrl+D abort signal."""
        self._ctrld.set()


def create_abort_signal() -> AbortSignal:
    """Create a new abort signal.

    Returns:
        New AbortSignal instance
    """
    return AbortSignal()


async def wait_abort_signal(abort_signal: AbortSignal) -> None:
    """Wait until the abort signal is triggered.

    Args:
        abort_signal: The abort signal to wait on
    """
    while not abort_signal.aborted():
        await asyncio.sleep(0.025)


async def wait_abort_signal_with_timeout(
    abort_signal: AbortSignal,
    timeout: float,
) -> bool:
    """Wait for abort signal with a timeout.

    Args:
        abort_signal: The abort signal to wait on
        timeout: Maximum time to wait in seconds

    Returns:
        True if aborted, False if timeout reached
    """
    try:
        await asyncio.wait_for(wait_abort_signal(abort_signal), timeout)
        return True
    except asyncio.TimeoutError:
        return False


class AbortChecker:
    """Context manager for checking abort status during operations.

    Example:
        async with AbortChecker(signal) as checker:
            while not checker.aborted:
                # Do work
                await asyncio.sleep(0.1)
    """

    def __init__(self, abort_signal: AbortSignal) -> None:
        """Initialize the checker.

        Args:
            abort_signal: The abort signal to check
        """
        self.abort_signal = abort_signal

    @property
    def aborted(self) -> bool:
        """Check if aborted."""
        return self.abort_signal.aborted()

    async def __aenter__(self) -> "AbortChecker":
        """Enter the context."""
        return self

    async def __aexit__(self, *args) -> None:
        """Exit the context."""
        pass


__all__ = [
    "AbortSignal",
    "create_abort_signal",
    "wait_abort_signal",
    "wait_abort_signal_with_timeout",
    "AbortChecker",
]
