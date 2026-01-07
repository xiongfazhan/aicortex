"""RAG (Retrieval-Augmented Generation) module.

Corresponds to src/rag/ in the Rust implementation.
"""

from .mod import (
    DocumentId,
    FileId,
    DocumentMetadata,
    RagFile,
    RagDocument,
    RagData,
    Rag,
    FaissIndex,
    Bm25Index,
)
from .splitter.mod import (
    RagDocument as SplitterDocument,
    DocumentMetadata as SplitterMetadata,
    SplitterChunkHeaderOptions,
    RecursiveCharacterTextSplitter,
    get_separators,
)
from .splitter.language import Language, DEFAULT_SEPARATORS, get_language
from .serde_vectors import serialize_vectors, deserialize_vectors

__all__ = [
    "DocumentId",
    "FileId",
    "DocumentMetadata",
    "RagFile",
    "RagDocument",
    "RagData",
    "Rag",
    "FaissIndex",
    "Bm25Index",
    "SplitterDocument",
    "SplitterMetadata",
    "SplitterChunkHeaderOptions",
    "RecursiveCharacterTextSplitter",
    "get_separators",
    "Language",
    "DEFAULT_SEPARATORS",
    "get_language",
    "serialize_vectors",
    "deserialize_vectors",
]
