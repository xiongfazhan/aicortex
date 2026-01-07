"""Document splitter module.

Corresponds to src/rag/splitter/ in the Rust implementation.
"""

from .mod import (
    RagDocument,
    DocumentMetadata,
    SplitterChunkHeaderOptions,
    RecursiveCharacterTextSplitter,
    get_separators,
)
from .language import Language, DEFAULT_SEPARATORS, get_language

__all__ = [
    "RagDocument",
    "DocumentMetadata",
    "SplitterChunkHeaderOptions",
    "RecursiveCharacterTextSplitter",
    "get_separators",
    "Language",
    "DEFAULT_SEPARATORS",
    "get_language",
]
