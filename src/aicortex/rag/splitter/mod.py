"""Document splitting for RAG.

Corresponds to src/rag/splitter/mod.rs in the Rust implementation.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import OrderedDict

from .language import Language, DEFAULT_SEPARATORS, get_language


@dataclass
class RagDocument:
    """A document chunk for RAG.

    Attributes:
        page_content: The text content of the document
        metadata: Associated metadata
    """

    page_content: str
    metadata: dict = field(default_factory=dict)

    @classmethod
    def new(cls, page_content: str) -> "RagDocument":
        """Create a new RagDocument.

        Args:
            page_content: The text content

        Returns:
            New RagDocument instance
        """
        return cls(page_content=page_content, metadata={})


# Type alias for metadata
DocumentMetadata = dict


@dataclass
class SplitterChunkHeaderOptions:
    """Options for chunk headers in document splitting.

    Attributes:
        chunk_header: Header to prepend to each chunk
        chunk_overlap_header: Header to prepend to overlapping chunks
    """

    chunk_header: str = ""
    chunk_overlap_header: Optional[str] = None


class RecursiveCharacterTextSplitter:
    """Split text into chunks recursively.

    Implements the LangChain RecursiveCharacterTextSplitter algorithm.
    Tries to split on different separators in order, preferring larger separators.

    Attributes:
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        separators: List of separators to try, in order
        length_function: Function to calculate text length
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 20,
        separators: Optional[list[str]] = None,
        length_function: Optional[Callable[[str], int]] = None,
    ):
        """Initialize the splitter.

        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
            separators: List of separators to try (default: DEFAULT_SEPARATORS)
            length_function: Function to calculate length (default: len)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators if separators is not None else list(DEFAULT_SEPARATORS)
        self.length_function = length_function if length_function is not None else len

    @classmethod
    def from_extension(cls, extension: str, chunk_size: int, chunk_overlap: int) -> "RecursiveCharacterTextSplitter":
        """Create a splitter with language-specific separators.

        Args:
            extension: File extension
            chunk_size: Maximum chunk size
            chunk_overlap: Chunk overlap

        Returns:
            RecursiveCharacterTextSplitter with appropriate separators
        """
        language = get_language(extension)
        if language:
            separators = language.separators()
        else:
            separators = list(DEFAULT_SEPARATORS)
        return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=separators)

    def split_documents(
        self,
        documents: list[RagDocument],
        chunk_header_options: SplitterChunkHeaderOptions,
    ) -> list[RagDocument]:
        """Split documents into chunks.

        Args:
            documents: List of documents to split
            chunk_header_options: Options for chunk headers

        Returns:
            List of split document chunks
        """
        texts: list[str] = []
        metadatas: list[DocumentMetadata] = []

        for doc in documents:
            if doc.page_content:
                texts.append(doc.page_content)
                metadatas.append(doc.metadata)

        return self.create_documents(texts, metadatas, chunk_header_options)

    def create_documents(
        self,
        texts: list[str],
        metadatas: list[DocumentMetadata],
        chunk_header_options: SplitterChunkHeaderOptions,
    ) -> list[RagDocument]:
        """Create document chunks from texts.

        Args:
            texts: List of text strings
            metadatas: List of metadata dictionaries
            chunk_header_options: Options for chunk headers

        Returns:
            List of RagDocument chunks
        """
        documents: list[RagDocument] = []

        for i, text in enumerate(texts):
            prev_chunk: Optional[str] = None
            index_prev_chunk = -1

            for chunk in self.split_text(text):
                page_content = chunk_header_options.chunk_header

                # Find chunk position in text
                if index_prev_chunk < 0:
                    index_chunk = text.find(chunk)
                else:
                    # Find next occurrence after previous position
                    offset = index_prev_chunk
                    remaining = text[offset:]
                    found = remaining.find(chunk)
                    if found >= 0:
                        index_chunk = offset + found
                    else:
                        index_chunk = -1

                if prev_chunk is not None and chunk_header_options.chunk_overlap_header:
                    page_content += chunk_header_options.chunk_overlap_header

                metadata = metadatas[i].copy() if i < len(metadatas) else {}
                page_content += chunk
                documents.append(RagDocument(page_content=page_content, metadata=metadata))

                prev_chunk = chunk
                index_prev_chunk = index_chunk

        return documents

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        keep_separator = any(any(c and not c.isspace() for c in s) for s in self.separators)
        return self._split_text_impl(text, self.separators, keep_separator)

    def _split_text_impl(
        self, text: str, separators: list[str], keep_separator: bool
    ) -> list[str]:
        """Internal implementation of text splitting.

        Args:
            text: Text to split
            separators: Separators to try
            keep_separator: Whether to keep separators in output

        Returns:
            List of text chunks
        """
        final_chunks: list[str] = []

        # Find the first separator that exists in the text
        separator = separators[-1] if separators else ""
        new_separators: list[str] = []

        for i, s in enumerate(separators):
            if not s:
                separator = s
                break
            if s in text:
                separator = s
                new_separators = separators[i + 1 :]
                break

        # Split on the chosen separator
        splits = self._split_on_separator(text, separator, keep_separator)

        # Recursively split longer texts
        good_splits: list[str] = []
        _separator = "" if keep_separator else separator

        for s in splits:
            if self.length_function(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged_text = self._merge_splits(good_splits, _separator)
                    final_chunks.extend(merged_text)
                    good_splits = []

                if not new_separators:
                    final_chunks.extend(self._split_by_length(s))
                else:
                    other_info = self._split_text_impl(s, new_separators, keep_separator)
                    final_chunks.extend(other_info)

        if good_splits:
            merged_text = self._merge_splits(good_splits, _separator)
            final_chunks.extend(merged_text)

        return final_chunks

    def _split_by_length(self, text: str) -> list[str]:
        """Split oversized text by length when no separators are available."""
        if self.length_function(text) <= self.chunk_size:
            return [text]

        overlap = min(self.chunk_overlap, max(self.chunk_size - 1, 0))
        step = max(self.chunk_size - overlap, 1)
        chunks = []
        for i in range(0, len(text), step):
            chunks.append(text[i : i + self.chunk_size])
        return [c for c in chunks if c]

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Merge splits into appropriately sized chunks.

        Args:
            splits: List of text splits
            separator: Separator to join with

        Returns:
            List of merged chunks
        """
        docs: list[str] = []
        current_doc: list[str] = []
        total = 0

        for d in splits:
            _len = self.length_function(d)

            if (
                total + _len + len(current_doc) * len(separator) > self.chunk_size
            ):
                if total > self.chunk_size:
                    pass  # Would warn about oversized chunk

                if current_doc:
                    doc = self._join_docs(current_doc, separator)
                    if doc is not None:
                        docs.append(doc)

                    # Remove chunks that exceed overlap
                    while (
                        total > self.chunk_overlap
                        or (
                            total + _len + len(current_doc) * len(separator) > self.chunk_size
                            and total > 0
                        )
                    ):
                        total -= self.length_function(current_doc[0])
                        current_doc.pop(0)

            current_doc.append(d)
            total += _len

        doc = self._join_docs(current_doc, separator)
        if doc is not None:
            docs.append(doc)

        return docs

    def _join_docs(self, docs: list[str], separator: str) -> Optional[str]:
        """Join docs with separator.

        Args:
            docs: List of document strings
            separator: Separator to join with

        Returns:
            Joined string or None if empty
        """
        text = separator.join(docs).strip()
        return text if text else None

    def _split_on_separator(self, text: str, separator: str, keep_separator: bool) -> list[str]:
        """Split text on separator.

        Args:
            text: Text to split
            separator: Separator string
            keep_separator: Whether to keep separator in output

        Returns:
            List of split parts
        """
        if not separator:
            return list(text)

        if keep_separator:
            splits = []
            prev_idx = 0
            sep_len = len(separator)

            while True:
                idx = text.find(separator, prev_idx)
                if idx == -1:
                    # Add final part
                    start = max(0, prev_idx - sep_len)
                    splits.append(text[start:])
                    break

                start = max(0, prev_idx - sep_len)
                splits.append(text[start : idx + sep_len])
                prev_idx = idx + sep_len
        else:
            splits = text.split(separator)

        return [s for s in splits if s]


def get_separators(extension: str) -> list[str]:
    """Get appropriate separators for a file extension.

    Args:
        extension: File extension

    Returns:
        List of separator strings
    """
    language = get_language(extension)
    if language:
        return language.separators()
    return list(DEFAULT_SEPARATORS)


__all__ = [
    "RagDocument",
    "DocumentMetadata",
    "SplitterChunkHeaderOptions",
    "RecursiveCharacterTextSplitter",
    "get_separators",
]
