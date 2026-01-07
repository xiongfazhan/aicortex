"""HTTP request utilities.

Corresponds to src/utils/request.rs in the Rust implementation.
"""

import asyncio
from typing import Optional
from dataclasses import dataclass


URL_LOADER = "url"
RECURSIVE_URL_LOADER = "recursive_url"
MEDIA_URL_EXTENSION = "media_url"
DEFAULT_EXTENSION = "txt"
USER_AGENT = "curl/8.6.0"

MAX_CRAWLS = 5
TIMEOUT = 16.0


async def fetch(url: str, timeout: float = TIMEOUT) -> str:
    """Fetch content from a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Response text

    Raises:
        IOError: If request fails

    Examples:
        >>> content = await fetch("https://example.com")
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            return response.text

    except ImportError:
        raise IOError("httpx is required for HTTP requests")


async def fetch_with_loaders(
    loaders: dict[str, str],
    path: str,
    allow_media: bool = False,
) -> tuple[str, str]:
    """Fetch content with custom loaders.

    Args:
        loaders: Dictionary of extension/protocol to loader commands
        path: URL or path to fetch
        allow_media: Whether to allow media content

    Returns:
        Tuple of (content, extension)

    Raises:
        IOError: If fetch fails
    """
    # Check for custom URL loader
    if URL_LOADER in loaders:
        loader_command = loaders[URL_LOADER]
        content = await _run_loader_command(path, loader_command)
        return (content, DEFAULT_EXTENSION)

    try:
        import httpx

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(path, headers={"User-Agent": USER_AGENT})

            if not response.status_code // 100 == 2:
                raise IOError(f"Invalid status: {response.status_code}")

            # Get content type
            content_type = response.headers.get("content-type", "")
            if ";" in content_type:
                mime_type = content_type.split(";", 1)[0].strip()
            else:
                mime_type = content_type

            # Determine extension from content type
            extension, is_media = _get_extension_from_mime(mime_type, path)

            if is_media and not allow_media:
                raise IOError("Unexpected media type")

            if is_media:
                # Handle media (encode as base64 data URL)
                import base64

                media_bytes = response.content
                media_base64 = base64.b64encode(media_bytes).decode("ascii")
                content = f"data:{content_type};base64,{media_base64}"
                return (content, extension)

            # Check for custom loader for this extension
            if extension in loaders:
                # Save to temp file and run loader
                import tempfile

                with tempfile.NamedTemporaryFile(
                    suffix=f".{extension}", delete=False
                ) as f:
                    temp_path = f.name
                    f.write(response.content)

                try:
                    loader_command = loaders[extension]
                    content = await _run_loader_command(temp_path, loader_command)
                    return (content, DEFAULT_EXTENSION)
                finally:
                    import os

                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass

            # Default: return text content
            content = response.text

            # Convert HTML to Markdown if needed
            if extension == "html":
                from ..utils.html_to_md import html_to_md

                content = html_to_md(content)
                return (content, "md")

            return (content, extension)

    except ImportError:
        raise IOError("httpx is required for HTTP requests")


def _get_extension_from_mime(mime_type: str, path: str) -> tuple[str, bool]:
    """Get file extension from MIME type.

    Args:
        mime_type: MIME type string
        path: Original path (fallback)

    Returns:
        Tuple of (extension, is_media)
    """
    import os

    # MIME type mappings
    mime_to_ext = {
        "application/pdf": ("pdf", False),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("docx", False),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ("xlsx", False),
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ("pptx", False),
        "application/vnd.oasis.opendocument.text": ("odt", False),
        "application/vnd.oasis.opendocument.spreadsheet": ("ods", False),
        "application/vnd.oasis.opendocument.presentation": ("odp", False),
        "application/rtf": ("rtf", False),
        "text/javascript": ("js", False),
        "text/html": ("html", False),
        "text/plain": ("txt", False),
        "text/markdown": ("md", False),
    }

    if mime_type in mime_to_ext:
        return mime_to_ext[mime_type]

    # Handle media types
    if "/" in mime_type:
        main_type, _ = mime_type.split("/", 1)
        if main_type in ("image", "video", "audio"):
            return (MEDIA_URL_EXTENSION, True)

        # Use subtype as extension
        _, subtype = mime_type.split("/", 1)
        return (subtype.lower(), False)

    # Fallback to path extension
    _, ext = os.path.splitext(path)
    if ext:
        return (ext.lstrip("."), False)

    return (DEFAULT_EXTENSION, False)


async def _run_loader_command(path: str, loader_command: str) -> str:
    """Run a loader command.

    Args:
        path: Path to load
        loader_command: Command template (use {path} for path)

    Returns:
        Command output

    Raises:
        IOError: If command fails
    """
    import os

    # Replace {path} placeholder
    cmd = loader_command.replace("{path}", path)

    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            raise IOError(f"Loader command failed: {error_msg}")

        return stdout.decode("utf-8", errors="replace")

    except Exception as e:
        raise IOError(f"Failed to run loader: {e}")


async def fetch_models(
    api_base: str,
    api_key: Optional[str] = None,
) -> list[str]:
    """Fetch available models from an API.

    Args:
        api_base: Base URL for the API
        api_key: Optional API key

    Returns:
        List of model IDs

    Raises:
        IOError: If fetch fails

    Examples:
        >>> models = await fetch_models("https://api.openai.com/v1", "sk-...")
    """
    try:
        import httpx

        api_base = api_base.rstrip("/")
        url = f"{api_base}/models"

        headers = {"User-Agent": USER_AGENT}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        models = []
        for item in data.get("data", []):
            model_id = item.get("id")
            if model_id:
                models.append(model_id)

        if not models:
            raise IOError("No valid models")

        models.sort()
        return models

    except ImportError:
        raise IOError("httpx is required for HTTP requests")
    except Exception as e:
        raise IOError(f"Failed to fetch models: {e}")


@dataclass
class Page:
    """A crawled page.

    Attributes:
        path: Page path/URL
        text: Page content
    """

    path: str
    text: str


@dataclass
class CrawlOptions:
    """Options for website crawling.

    Attributes:
        extract: CSS selector for content extraction
        exclude: List of patterns to exclude
        no_log: Disable logging
    """

    extract: Optional[str] = None
    exclude: list[str] = None
    no_log: bool = False

    def __post_init__(self) -> None:
        if self.exclude is None:
            self.exclude = []


async def crawl_website(
    start_url: str,
    options: Optional[CrawlOptions] = None,
) -> list[Page]:
    """Crawl a website and extract pages.

    Args:
        start_url: Starting URL
        options: Crawl options

    Returns:
        List of crawled pages

    Raises:
        IOError: If crawling fails
    """
    # Simplified implementation - just fetch the single page
    if options is None:
        options = CrawlOptions()

    try:
        content = await fetch(start_url)

        # If HTML, try to extract with selector or convert to markdown
        if start_url.endswith(".html") or "html" in start_url:
            if options.extract:
                # Would use BeautifulSoup here for CSS selector extraction
                pass
            else:
                from ..utils.html_to_md import html_to_md

                content = html_to_md(content)

        return [Page(path=start_url, text=content)]

    except Exception as e:
        raise IOError(f"Failed to crawl {start_url}: {e}")


__all__ = [
    "URL_LOADER",
    "RECURSIVE_URL_LOADER",
    "MEDIA_URL_EXTENSION",
    "DEFAULT_EXTENSION",
    "USER_AGENT",
    "MAX_CRAWLS",
    "TIMEOUT",
    "fetch",
    "fetch_with_loaders",
    "fetch_models",
    "Page",
    "CrawlOptions",
    "crawl_website",
]
