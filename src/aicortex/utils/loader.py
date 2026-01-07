"""Document loader utilities.

Corresponds to src/utils/loader.rs in the Rust implementation.
"""

import os
import asyncio
import subprocess
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
from urllib.parse import urlparse


EXTENSION_METADATA = "__extension__"
DEFAULT_EXTENSION = "txt"
RECURSIVE_URL_LOADER = "rurl"


@dataclass
class LoadedDocument:
    """A loaded document with metadata.

    Attributes:
        path: Document path or URL
        contents: Document content
        metadata: Document metadata
    """

    path: str
    contents: str
    metadata: "OrderedDict[str, str]" = field(default_factory=OrderedDict)

    @classmethod
    def new(
        cls,
        path: str,
        contents: str,
        metadata: "OrderedDict[str, str]",
    ) -> "LoadedDocument":
        """Create a new LoadedDocument.

        Args:
            path: Document path
            contents: Document contents
            metadata: Document metadata

        Returns:
            New LoadedDocument instance
        """
        return cls(path=path, contents=contents, metadata=metadata)


def get_file_extension(path: str) -> Optional[str]:
    """Get file extension from path.

    Args:
        path: File path or URL

    Returns:
        File extension without dot, or None
    """
    # Handle URLs
    if "://" in path:
        parsed = urlparse(path)
        path = parsed.path

    # Get extension
    _, ext = os.path.splitext(path)
    if ext:
        return ext.lstrip(".")
    return None


async def load_file(
    loaders: dict[str, str],
    path: str,
) -> LoadedDocument:
    """Load a document from a file path.

    Args:
        loaders: Dictionary of file extension to loader command
        path: File path to load

    Returns:
        LoadedDocument instance

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")

    extension = get_file_extension(path) or DEFAULT_EXTENSION

    # Check if there's a custom loader
    if extension in loaders:
        return await load_with_command(path, extension, loaders[extension])

    # Load plain text
    content = path_obj.read_text(encoding="utf-8")

    metadata = OrderedDict()
    metadata[EXTENSION_METADATA] = extension

    return LoadedDocument.new(path, content, metadata)


async def load_url(
    loaders: dict[str, str],
    url: str,
) -> LoadedDocument:
    """Load a document from a URL.

    Args:
        loaders: Dictionary of protocol to loader command
        url: URL to fetch

    Returns:
        LoadedDocument instance

    Raises:
        IOError: If URL cannot be fetched
    """
    extension = get_file_extension(url) or DEFAULT_EXTENSION

    # Check for custom loader
    parsed = urlparse(url)
    if parsed.scheme in loaders:
        loader_command = loaders[parsed.scheme]
        return await load_with_command(url, parsed.scheme, loader_command)

    # Default HTTP fetch
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text

        metadata = OrderedDict()
        metadata[EXTENSION_METADATA] = extension

        return LoadedDocument.new(url, content, metadata)

    except ImportError:
        raise IOError("httpx is required for URL loading")


async def load_with_command(
    path: str,
    extension: str,
    loader_command: str,
) -> LoadedDocument:
    """Load a document using an external command.

    Args:
        path: File path to load
        extension: File extension
        loader_command: Command to run for loading

    Returns:
        LoadedDocument instance

    Raises:
        IOError: If command fails
    """
    try:
        process = await asyncio.create_subprocess_shell(
            f"{loader_command} {path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            raise IOError(f"Loader command failed: {error_msg}")

        content = stdout.decode("utf-8", errors="replace")

        metadata = OrderedDict()
        metadata[EXTENSION_METADATA] = DEFAULT_EXTENSION

        return LoadedDocument.new(path, content, metadata)

    except Exception as e:
        raise IOError(f"Failed to load with command: {e}")


def is_loader_protocol(loaders: dict[str, str], path: str) -> bool:
    """Check if path uses a loader protocol.

    Args:
        loaders: Dictionary of protocol to loader command
        path: Path to check

    Returns:
        True if path uses a known loader protocol
    """
    if ":" not in path:
        return False

    protocol = path.split(":", 1)[0]
    return protocol in loaders


async def load_protocol_path(
    loaders: dict[str, str],
    path: str,
) -> list[LoadedDocument]:
    """Load documents using a protocol loader.

    Args:
        loaders: Dictionary of protocol to loader command
        path: Protocol path (e.g., "s3:bucket/key")

    Returns:
        List of LoadedDocument instances

    Raises:
        IOError: If loading fails
    """
    if ":" not in path:
        raise IOError(f"Invalid protocol path: {path}")

    protocol, remaining = path.split(":", 1)

    if protocol not in loaders:
        raise IOError(f"No loader for protocol: {protocol}")

    loader_command = loaders[protocol]

    try:
        process = await asyncio.create_subprocess_shell(
            f"{loader_command} {remaining}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            raise IOError(f"Loader command failed: {error_msg}")

        content = stdout.decode("utf-8", errors="replace")

        # Try to parse as JSON array of documents
        try:
            import json

            docs_data = json.loads(content)
            return [
                LoadedDocument.new(
                    doc.get("path", path),
                    doc.get("text", doc.get("content", "")),
                    OrderedDict(doc.get("metadata", {})),
                )
                for doc in docs_data
            ]
        except json.JSONDecodeError:
            # Return as single document
            return [LoadedDocument.new(path, content, OrderedDict())]

    except Exception as e:
        raise IOError(f"Failed to load protocol path: {e}")


async def load_document(
    loaders: dict[str, str],
    path: str,
) -> LoadedDocument:
    """Load a document from file or URL.

    Automatically detects the type of path and uses the appropriate loader.

    Args:
        loaders: Dictionary of extension/protocol to loader commands
        path: File path, URL, or protocol path

    Returns:
        LoadedDocument instance

    Raises:
        FileNotFoundError: If file not found
        IOError: If loading fails
    """
    # Check for protocol path
    if is_loader_protocol(loaders, path):
        docs = await load_protocol_path(loaders, path)
        if docs:
            return docs[0]
        raise IOError(f"No documents loaded from: {path}")

    # Check for URL
    if "://" in path:
        return await load_url(loaders, path)

    # Otherwise, treat as file path
    return await load_file(loaders, path)


__all__ = [
    "EXTENSION_METADATA",
    "DEFAULT_EXTENSION",
    "RECURSIVE_URL_LOADER",
    "LoadedDocument",
    "get_file_extension",
    "load_file",
    "load_url",
    "load_with_command",
    "is_loader_protocol",
    "load_protocol_path",
    "load_document",
]
