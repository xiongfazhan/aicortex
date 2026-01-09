"""RAG (Retrieval-Augmented Generation) module.

Corresponds to src/rag/mod.rs in the Rust implementation.
"""

import asyncio
import yaml
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from collections import OrderedDict
from pathlib import Path
from abc import ABC, abstractmethod
from ..utils import estimate_token_length

CODE_EXTENSIONS = {
    "py", "js", "ts", "tsx", "jsx", "java", "go", "rs", "cpp", "c", "h", "hpp",
    "cs", "php", "rb", "swift", "kt", "kts", "scala", "lua", "sql", "sh", "ps1",
}

TEXT_EXTENSIONS = {
    "txt", "log", "ini", "cfg", "conf", "yaml", "yml", "toml", "csv",
}

try:
    import faiss
    import numpy as np
    from rank_bm25 import BM25Okapi
except ImportError:
    faiss = None
    np = None
    BM25Okapi = None

from .splitter.mod import (
    RagDocument,
    RecursiveCharacterTextSplitter,
    SplitterChunkHeaderOptions,
    get_separators,
)
from .serde_vectors import DocumentId, serialize_vectors, deserialize_vectors


# Type aliases
FileId = int
DocumentMetadata = dict


def _split_markdown_sections(text: str) -> list[tuple[Optional[str], str]]:
    """Split markdown into sections by headings, ignoring fenced code blocks."""
    sections: list[tuple[Optional[str], str]] = []
    current: list[str] = []
    current_title: Optional[str] = None
    in_code_block = False

    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block

        if not in_code_block and stripped.startswith("#"):
            if current:
                section = "\n".join(current).strip()
                if section:
                    sections.append((current_title, section))
                current = []
            current_title = stripped.lstrip("#").strip() or None

        current.append(line)

    if current:
        section = "\n".join(current).strip()
        if section:
            sections.append((current_title, section))

    return sections


def _split_paragraphs(text: str) -> list[str]:
    """Split text by blank lines into paragraphs."""
    paragraphs = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line)
        else:
            if current:
                paragraphs.append("\n".join(current).strip())
                current = []
    if current:
        paragraphs.append("\n".join(current).strip())
    return [p for p in paragraphs if p]


def _split_text_by_type(extension: str, content: str) -> list[tuple[Optional[str], str]]:
    """Split content by document type into base sections."""
    if extension in ("md", "markdown", "mdx"):
        return _split_markdown_sections(content)

    if extension in CODE_EXTENSIONS:
        blocks = _split_paragraphs(content)
        return [(None, block) for block in blocks]

    if extension in TEXT_EXTENSIONS:
        paragraphs = _split_paragraphs(content)
        return [(None, p) for p in paragraphs]

    return [(None, content)]


def _split_text_by_strategy(
    strategy: str, extension: str, content: str
) -> list[tuple[Optional[str], str]]:
    """Split content based on configured strategy."""
    strategy = (strategy or "auto").lower()
    if strategy == "plain":
        return [(None, content)]
    if strategy == "markdown":
        return _split_markdown_sections(content)
    if strategy == "code":
        blocks = _split_paragraphs(content)
        return [(None, block) for block in blocks]
    if strategy == "text":
        paragraphs = _split_paragraphs(content)
        return [(None, p) for p in paragraphs]
    return _split_text_by_type(extension, content)


@dataclass
class RagFile:
    """A file in the RAG index.

    Attributes:
        hash: SHA256 hash of file contents
        path: Original file path
        documents: List of document chunks
    """

    hash: str
    path: str
    documents: list[RagDocument] = field(default_factory=list)


@dataclass
class RagData:
    """Core data for RAG.

    Attributes:
        embedding_model: ID of the embedding model
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        reranker_model: Optional reranker model ID
        top_k: Number of results to return
        batch_size: Batch size for embeddings
        next_file_id: Next file ID to assign
        document_paths: List of document paths
        files: Mapping of file IDs to RagFile
        vectors: Mapping of document IDs to embeddings
    """

    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    reranker_model: Optional[str]
    top_k: int
    batch_size: Optional[int]
    next_file_id: FileId = 0
    document_paths: list[str] = field(default_factory=list)
    files: "OrderedDict[FileId, RagFile]" = field(default_factory=OrderedDict)
    vectors: "OrderedDict[DocumentId, list[float]]" = field(default_factory=OrderedDict)

    @classmethod
    def new(
        cls,
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
        reranker_model: Optional[str],
        top_k: int,
        batch_size: Optional[int],
    ) -> "RagData":
        """Create new RagData.

        Args:
            embedding_model: ID of embedding model
            chunk_size: Chunk size for splitting
            chunk_overlap: Chunk overlap
            reranker_model: Optional reranker model
            top_k: Number of top results
            batch_size: Batch size for embeddings

        Returns:
            New RagData instance
        """
        return cls(
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            reranker_model=reranker_model,
            top_k=top_k,
            batch_size=batch_size,
        )

    def get(self, id: DocumentId) -> Optional[RagDocument]:
        """Get a document by ID.

        Args:
            id: Document ID

        Returns:
            RagDocument or None if not found
        """
        file_index, document_index = id.split()
        file = self.files.get(file_index)
        if file is None:
            return None
        if document_index >= len(file.documents):
            return None
        return file.documents[document_index]

    def del_files(self, file_ids: list[FileId]) -> None:
        """Delete files and their associated vectors.

        Args:
            file_ids: List of file IDs to delete
        """
        for file_id in file_ids:
            file = self.files.pop(file_id, None)
            if file:
                for document_index in range(len(file.documents)):
                    doc_id = DocumentId(file_id, document_index)
                    self.vectors.pop(doc_id, None)

    def add(
        self,
        next_file_id: FileId,
        files: list[tuple[FileId, RagFile]],
        document_ids: list[DocumentId],
        embeddings: list[list[float]],
    ) -> None:
        """Add new files and embeddings.

        Args:
            next_file_id: Next file ID to use
            files: List of (file_id, RagFile) tuples
            document_ids: List of document IDs
            embeddings: List of embedding vectors
        """
        self.next_file_id = next_file_id
        for file_id, rag_file in files:
            self.files[file_id] = rag_file
        for doc_id, embedding in zip(document_ids, embeddings):
            self.vectors[doc_id] = embedding

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization.

        Returns:
            Dictionary representation
        """
        return {
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "reranker_model": self.reranker_model,
            "top_k": self.top_k,
            "batch_size": self.batch_size,
            "next_file_id": self.next_file_id,
            "document_paths": self.document_paths,
            "files": {
                str(k): {
                    "hash": v.hash,
                    "path": v.path,
                    "documents": [
                        {"page_content": d.page_content, "metadata": d.metadata}
                        for d in v.documents
                    ],
                }
                for k, v in self.files.items()
            },
            "vectors": serialize_vectors(self.vectors),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RagData":
        """Create from dictionary.

        Args:
            data: Dictionary from YAML deserialization

        Returns:
            RagData instance
        """
        files = OrderedDict()
        for k, v in data.get("files", {}).items():
            file_id = int(k)
            files[file_id] = RagFile(
                hash=v["hash"],
                path=v["path"],
                documents=[
                    RagDocument(
                        page_content=d["page_content"], metadata=d.get("metadata", {})
                    )
                    for d in v["documents"]
                ],
            )

        vectors = deserialize_vectors(data.get("vectors", {}))

        return cls(
            embedding_model=data["embedding_model"],
            chunk_size=data["chunk_size"],
            chunk_overlap=data["chunk_overlap"],
            reranker_model=data.get("reranker_model"),
            top_k=data["top_k"],
            batch_size=data.get("batch_size"),
            next_file_id=data.get("next_file_id", 0),
            document_paths=data.get("document_paths", []),
            files=files,
            vectors=vectors,
        )


class RagIndex(ABC):
    """Abstract base class for RAG index."""

    @abstractmethod
    def search(self, vector: list[float], top_k: int) -> list[tuple[DocumentId, float]]:
        """Search for similar vectors.

        Args:
            vector: Query vector
            top_k: Number of results to return

        Returns:
            List of (DocumentId, score) tuples
        """
        pass


class FaissIndex(RagIndex):
    """FAISS-based vector index."""

    def __init__(self, dimension: int):
        """Initialize FAISS index.

        Args:
            dimension: Vector dimension
        """
        if faiss is None:
            raise ImportError("faiss-cpu is required for FaissIndex")
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.doc_ids: list[DocumentId] = []

    def build(self, vectors: "OrderedDict[DocumentId, list[float]]") -> None:
        """Build the index from vectors.

        Args:
            vectors: Mapping of document IDs to vectors
        """
        if not vectors:
            return

        # Get vector dimension from first vector
        first_vec = next(iter(vectors.values()))
        self.dimension = len(first_vec)

        # Create FAISS index (inner product for cosine similarity)
        self.index = faiss.IndexFlatIP(self.dimension)

        # Prepare data
        doc_vectors = []
        self.doc_ids = list(vectors.keys())
        for doc_id in self.doc_ids:
            vec = vectors[doc_id]
            # Normalize for cosine similarity
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec_normalized = [v / norm for v in vec]
            else:
                vec_normalized = vec
            doc_vectors.append(vec_normalized)

        # Add to index
        numpy_array = np.array(doc_vectors, dtype=np.float32)
        self.index.add(numpy_array)

    def search(self, vector: list[float], top_k: int) -> list[tuple[DocumentId, float]]:
        """Search for similar vectors.

        Args:
            vector: Query vector
            top_k: Number of results

        Returns:
            List of (DocumentId, score) tuples
        """
        if self.index is None or not self.doc_ids:
            return []

        # Normalize query vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            query = np.array([[v / norm for v in vector]], dtype=np.float32)
        else:
            query = np.array([vector], dtype=np.float32)

        # Search
        k = min(top_k, len(self.doc_ids))
        scores, indices = self.index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.doc_ids):
                doc_id = self.doc_ids[int(idx)]
                results.append((doc_id, float(score)))

        return results


class Bm25Index:
    """BM25-based keyword search index."""

    def __init__(self):
        """Initialize BM25 index."""
        self.doc_ids: list[DocumentId] = []
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_docs: list[list[str]] = []

    def build(self, data: RagData) -> None:
        """Build the BM25 index.

        Args:
            data: RagData containing documents
        """
        if BM25Okapi is None:
            raise ImportError("rank-bm25 is required for Bm25Index")

        documents: list[tuple[DocumentId, str]] = []
        for file_index, file in data.files.items():
            for document_index, document in enumerate(file.documents):
                doc_id = DocumentId(file_index, document_index)
                documents.append((doc_id, document.page_content))

        if not documents:
            return

        self.doc_ids = [doc_id for doc_id, _ in documents]
        texts = [text for _, text in documents]

        # Tokenize documents
        self.tokenized_docs = [text.lower().split() for text in texts]

        # Build BM25 index
        self.bm25 = BM25Okapi(self.tokenized_docs, k1=1.5, b=0.75)

    def search(self, query: str, top_k: int) -> list[tuple[DocumentId, float]]:
        """Search for relevant documents.

        Args:
            query: Query string
            top_k: Number of results

        Returns:
            List of (DocumentId, score) tuples
        """
        if self.bm25 is None or not self.doc_ids:
            return []

        # Tokenize query
        tokenized_query = query.lower().split()

        # Search
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k
        indexed_scores = [(i, score) for i, score in enumerate(scores) if score > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for i, score in indexed_scores[:top_k]:
            doc_id = self.doc_ids[i]
            results.append((doc_id, float(score)))

        return results


class Rag:
    """RAG (Retrieval-Augmented Generation) system.

    Provides document indexing and retrieval for augmenting LLM responses.

    Attributes:
        name: RAG name
        path: Path to RAG file
        data: RAG data
        faiss_index: FAISS vector index
        bm25_index: BM25 keyword index
    """

    TEMP_RAG_NAME = "_temp_"

    def __init__(
        self,
        name: str,
        path: str,
        data: RagData,
    ):
        """Initialize Rag.

        Args:
            name: RAG name
            path: Path to RAG storage
            data: RAG data
        """
        self.name = name
        self.path = path
        self.data = data
        self.faiss_index: Optional[FaissIndex] = None
        self.bm25_index: Optional[Bm25Index] = None
        self.last_sources: Optional[str] = None

        self._build_indexes()

    def _build_indexes(self) -> None:
        """Build search indexes."""
        # Build FAISS index
        if self.data.vectors:
            first_vec = next(iter(self.data.vectors.values()))
            self.faiss_index = FaissIndex(len(first_vec))
            self.faiss_index.build(self.data.vectors)

        # Build BM25 index
        self.bm25_index = Bm25Index()
        self.bm25_index.build(self.data)

    @classmethod
    def load(cls, path: str) -> "Rag":
        """Load RAG from file.

        Args:
            path: Path to RAG YAML file

        Returns:
            Rag instance
        """
        content = Path(path).read_text(encoding="utf-8")
        data_dict = yaml.safe_load(content)
        data = RagData.from_dict(data_dict)
        return cls(name=Path(path).stem, path=path, data=data)

    def save(self, path: Optional[str] = None) -> bool:
        """Save RAG to file.

        Args:
            path: Optional path to save to (default: self.path)

        Returns:
            True if saved, False if temp RAG
        """
        if self.is_temp():
            return False

        save_path = path or self.path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self.data.to_dict(), f, default_flow_style=False, allow_unicode=True)

        return True

    def document_paths(self) -> list[str]:
        """Get document paths.

        Returns:
            List of document paths
        """
        return self.data.document_paths

    def name(self) -> str:
        """Get RAG name.

        Returns:
            RAG name
        """
        return self.name

    def is_temp(self) -> bool:
        """Check if this is a temporary RAG.

        Returns:
            True if temporary
        """
        return self.name == self.TEMP_RAG_NAME

    def get_config(self) -> tuple[Optional[str], int]:
        """Get reranker config.

        Returns:
            Tuple of (reranker_model, top_k)
        """
        return self.data.reranker_model, self.data.top_k

    def get_last_sources(self) -> Optional[str]:
        """Get last search sources.

        Returns:
            Formatted sources string or None
        """
        return self.last_sources

    def set_last_sources(self, ids: list[DocumentId]) -> None:
        """Set last search sources.

        Args:
            ids: List of document IDs
        """
        sources: dict[str, list[str]] = {}
        for doc_id in ids:
            file_index, _ = doc_id.split()
            file = self.data.files.get(file_index)
            if file:
                sources.setdefault(file.path, []).append(str(doc_id))

        if sources:
            self.last_sources = "\n".join(
                f"{path} ({','.join(ids)})" for path, ids in sources.items()
            )
        else:
            self.last_sources = None

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        config: Any = None,
    ) -> tuple[str, list[DocumentId]]:
        """Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results (default: from config)
            config: Config for embedding client

        Returns:
            Tuple of (joined_results, document_ids)
        """
        if top_k is None:
            if config is not None and getattr(config, "rag_top_k", None):
                top_k = config.rag_top_k
            else:
                top_k = self.data.top_k

        # Perform hybrid search
        ids = await self._hybrid_search(query, top_k, config)
        self.set_last_sources(ids)

        # Get documents
        documents = []
        for doc_id in ids:
            doc = self.data.get(doc_id)
            if doc:
                documents.append(doc.page_content)

        return "\n\n".join(documents), ids

    async def _hybrid_search(
        self, query: str, top_k: int, config: Any = None
    ) -> list[DocumentId]:
        """Perform hybrid vector + keyword search.

        Args:
            query: Search query
            top_k: Number of results
            config: Config for embedding client

        Returns:
            List of document IDs
        """
        vector_top_k = getattr(config, "rag_vector_top_k", top_k) if config else top_k
        bm25_top_k = getattr(config, "rag_bm25_top_k", top_k) if config else top_k
        candidate_k = getattr(config, "rag_candidate_k", top_k) if config else top_k
        file_cap = getattr(config, "rag_file_cap", 0) if config else 0
        section_cap = getattr(config, "rag_section_cap", 0) if config else 0
        rerank_top_k = getattr(config, "rag_rerank_top_k", top_k) if config else top_k
        parent_min = getattr(config, "rag_parent_min_tokens", 0) if config else 0
        parent_max = getattr(config, "rag_parent_max_tokens", 0) if config else 0

        # Vector search
        vector_results = await self._vector_search(query, vector_top_k, 0.0, config)

        # Keyword search
        keyword_results = self._keyword_search(query, bm25_top_k, 0.0)

        # Combine using reciprocal rank fusion
        rrf_top_k = max(vector_top_k, bm25_top_k, candidate_k * 2)
        combined = self._reciprocal_rank_fusion(
            [vector_results, keyword_results],
            [1.125, 1.0],
            rrf_top_k,
        )

        candidates = self._apply_coverage_caps(
            combined,
            candidate_k,
            file_cap,
            section_cap,
        )

        reranked = await self._rerank_candidates(query, candidates, rerank_top_k, config)

        if parent_max:
            return self._expand_with_parents(reranked, parent_min, parent_max)

        return reranked

    def _apply_coverage_caps(
        self,
        candidates: list[DocumentId],
        candidate_k: int,
        file_cap: int,
        section_cap: int,
    ) -> list[DocumentId]:
        """Apply per-file and per-section caps to candidates."""
        results: list[DocumentId] = []
        file_counts: dict[int, int] = {}
        section_counts: dict[tuple[int, str], int] = {}

        for doc_id in candidates:
            file_id, _ = doc_id.split()
            if file_cap > 0 and file_counts.get(file_id, 0) >= file_cap:
                continue

            doc = self.data.get(doc_id)
            section = None
            if doc and isinstance(doc.metadata, dict):
                section = doc.metadata.get("section")

            if section and section_cap > 0:
                key = (file_id, section)
                if section_counts.get(key, 0) >= section_cap:
                    continue

            results.append(doc_id)
            file_counts[file_id] = file_counts.get(file_id, 0) + 1
            if section:
                key = (file_id, section)
                section_counts[key] = section_counts.get(key, 0) + 1

            if len(results) >= candidate_k:
                break

        return results

    async def _rerank_candidates(
        self,
        query: str,
        candidates: list[DocumentId],
        top_k: int,
        config: Any = None,
    ) -> list[DocumentId]:
        """Rerank candidates using reranker model if available."""
        if not candidates:
            return []

        reranker_model_id = None
        if config and getattr(config, "rag_reranker_model", None):
            reranker_model_id = config.rag_reranker_model
        elif self.data.reranker_model:
            reranker_model_id = self.data.reranker_model

        if not reranker_model_id or config is None:
            return candidates[:top_k]

        client = await self._get_rerank_client(config, reranker_model_id)
        if client is None:
            return candidates[:top_k]

        documents = []
        for doc_id in candidates:
            doc = self.data.get(doc_id)
            documents.append(doc.page_content if doc else "")

        try:
            from ..client import RerankData
            data = RerankData(
                query=query,
                documents=documents,
                top_n=top_k,
                model=client.model.real_name(),
            )
            results = await client.rerank(data)
        except Exception as e:
            print(f"Warning: rerank failed: {e}")
            return candidates[:top_k]

        if not results:
            return candidates[:top_k]

        ranked = sorted(
            results, key=lambda r: r.get("relevance_score", 0), reverse=True
        )
        reranked_ids = [
            candidates[item["index"]]
            for item in ranked
            if 0 <= item.get("index", -1) < len(candidates)
        ]

        return reranked_ids[:top_k]

    def _expand_with_parents(
        self,
        doc_ids: list[DocumentId],
        min_tokens: int,
        max_tokens: int,
    ) -> list[DocumentId]:
        """Expand hits with adjacent chunks within token budget."""
        if not doc_ids:
            return []

        results: list[DocumentId] = []
        seen: set[DocumentId] = set()
        total_tokens = 0

        for doc_id in doc_ids:
            file_id, doc_index = doc_id.split()
            file = self.data.files.get(file_id)
            if not file:
                continue

            neighbors = []
            if doc_index - 1 >= 0:
                neighbors.append(DocumentId(file_id, doc_index - 1))
            neighbors.append(doc_id)
            if doc_index + 1 < len(file.documents):
                neighbors.append(DocumentId(file_id, doc_index + 1))

            for neighbor_id in neighbors:
                if neighbor_id in seen:
                    continue
                doc = self.data.get(neighbor_id)
                if not doc:
                    continue
                doc_tokens = estimate_token_length(doc.page_content)
                if max_tokens and total_tokens + doc_tokens > max_tokens:
                    continue
                results.append(neighbor_id)
                seen.add(neighbor_id)
                total_tokens += doc_tokens

            if max_tokens and total_tokens >= max_tokens:
                break

        if min_tokens and total_tokens < min_tokens:
            return results

        return results

    async def _get_rerank_client(self, config: Any, model_id: str) -> Optional[Any]:
        """Get rerank client from config."""
        if ":" in model_id:
            provider, model_name = model_id.split(":", 1)
        else:
            provider = "openai"
            model_name = model_id

        client_config = config.get_client_config(provider)
        if not client_config:
            return None

        api_key = client_config.get("api_key", "")

        model = None
        if hasattr(config, "resolve_model"):
            try:
                model = await config.resolve_model(model_id)
            except Exception:
                model = None

        if model is None:
            from ..client import Model
            model = Model.new(provider, model_name)

        api_base = model.api_base() or client_config.get("api_base")

        from ..llm import create_client
        return await create_client(provider, api_key, model, api_base)

    async def _vector_search(
        self, query: str, top_k: int, min_score: float, config: Any = None
    ) -> list[tuple[DocumentId, float]]:
        """Perform vector similarity search.

        Args:
            query: Query string
            top_k: Number of results
            min_score: Minimum score threshold
            config: Config object with embedding model info

        Returns:
            List of (DocumentId, score) tuples
        """
        if self.faiss_index is None or not self.data.vectors:
            return []

        # Get query embedding
        query_embedding = await self._get_query_embedding(query, config)
        if not query_embedding:
            return []

        # Search FAISS index
        results = self.faiss_index.search(query_embedding, top_k)
        return [(doc_id, score) for doc_id, score in results if score > min_score]

    async def _get_query_embedding(self, query: str, config: Any = None) -> Optional[list[float]]:
        """Get embedding for query text.

        Args:
            query: Query text
            config: Config with embedding model info

        Returns:
            Embedding vector or None
        """
        if config is None:
            return None

        try:
            client = await self._get_embedding_client(config)
            if client is None:
                return None

            from ..client import EmbeddingsData
            data = EmbeddingsData(texts=[query], query=True, input_type="query", truncate="NONE")
            embeddings = await client.embeddings(data)
            return embeddings[0] if embeddings else None
        except Exception as e:
            print(f"Error getting query embedding: {e}")
            return None

    async def _get_embedding_client(self, config: Any) -> Optional[Any]:
        """Get embedding client from config.

        Args:
            config: Config with embedding model info

        Returns:
            Client instance or None
        """
        embedding_model_id = config.rag_embedding_model or self.data.embedding_model
        if not embedding_model_id:
            return None

        # Parse provider:model format
        if ":" in embedding_model_id:
            provider, model_name = embedding_model_id.split(":", 1)
        else:
            provider = "openai"
            model_name = embedding_model_id

        # Get client config
        client_config = config.get_client_config(provider)
        if not client_config:
            return None

        api_key = client_config.get("api_key", "")

        # Create model (prefer config-defined model for per-model overrides)
        model = None
        if hasattr(config, "resolve_model"):
            try:
                model = await config.resolve_model(embedding_model_id)
            except Exception:
                model = None

        if model is None:
            from ..client import Model
            model = Model.new(provider, model_name)

        api_base = model.api_base() or client_config.get("api_base")

        # Create client
        from ..llm import create_client
        return await create_client(provider, api_key, model, api_base)

    async def build_from_paths(self, config: Any) -> int:
        """Build RAG from document paths.

        Reads files, splits into chunks, generates embeddings.

        Args:
            config: Config with embedding model info

        Returns:
            Number of documents processed
        """
        import hashlib
        from pathlib import Path as FilePath

        pending_paths = [
            p for p in self.data.document_paths
            if not any(f.path == p for f in self.data.files.values())
        ]

        if not pending_paths:
            return 0

        # Get embedding client
        client = await self._get_embedding_client(config)
        if client is None:
            raise ValueError("Could not create embedding client")

        # Resolve embedding model for token limit hints
        embedding_model_id = config.rag_embedding_model or self.data.embedding_model
        embedding_model = None
        if embedding_model_id and hasattr(config, "resolve_model"):
            try:
                embedding_model = await config.resolve_model(embedding_model_id)
            except Exception:
                embedding_model = None

        processed = 0
        next_file_id = self.data.next_file_id

        for doc_path in pending_paths:
            path = FilePath(doc_path)
            if not path.exists():
                print(f"Warning: File not found: {doc_path}")
                continue

            # Read file content
            try:
                content = path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Warning: Could not read {doc_path}: {e}")
                continue

            # Calculate hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()

            # Split into chunks
            extension = path.suffix.lstrip(".")
            effective_chunk_size = (
                config.rag_chunk_size if config and getattr(config, "rag_chunk_size", None)
                else self.data.chunk_size
            )
            effective_chunk_overlap = (
                config.rag_chunk_overlap if config and getattr(config, "rag_chunk_overlap", None)
                else self.data.chunk_overlap
            )
            if embedding_model is not None:
                max_tokens = embedding_model.max_tokens_per_chunk() or embedding_model.max_input_tokens()
                if max_tokens and max_tokens < effective_chunk_size:
                    effective_chunk_size = max_tokens

            splitter = RecursiveCharacterTextSplitter.from_extension(
                extension,
                effective_chunk_size,
                effective_chunk_overlap,
            )

            from .splitter.mod import RagDocument as SplitterDoc, SplitterChunkHeaderOptions
            split_strategy = (
                config.rag_split_strategy
                if config and getattr(config, "rag_split_strategy", None)
                else "auto"
            )
            base_sections = _split_text_by_strategy(split_strategy, extension, content)

            chunks: list[tuple[Optional[str], str]] = []
            for section_title, text in base_sections:
                for chunk in splitter.split_text(text):
                    chunks.append((section_title, chunk))

            if not chunks:
                continue

            # Create RagDocuments
            documents = [
                RagDocument(page_content=chunk, metadata={"section": section_title})
                for section_title, chunk in chunks
            ]

            # Generate embeddings
            try:
                from ..client import EmbeddingsData
                data = EmbeddingsData(
                    texts=[chunk for _, chunk in chunks],
                    query=False,
                    input_type="passage",
                    truncate="NONE"
                )
                embeddings = await client.embeddings(data)
            except Exception as e:
                print(f"Warning: Could not generate embeddings for {doc_path}: {e}")
                continue

            # Create RagFile
            rag_file = RagFile(
                hash=file_hash,
                path=doc_path,
                documents=documents,
            )

            # Add to data
            file_id = next_file_id
            next_file_id += 1

            self.data.files[file_id] = rag_file

            # Store embeddings
            for doc_idx, embedding in enumerate(embeddings):
                doc_id = DocumentId(file_id, doc_idx)
                self.data.vectors[doc_id] = embedding

            processed += 1
            print(f"  Processed: {path.name} ({len(chunks)} chunks)")

        self.data.next_file_id = next_file_id

        # Rebuild indexes
        self._build_indexes()

        return processed

    def _keyword_search(
        self, query: str, top_k: int, min_score: float
    ) -> list[tuple[DocumentId, float]]:
        """Perform BM25 keyword search.

        Args:
            query: Query string
            top_k: Number of results
            min_score: Minimum score threshold

        Returns:
            List of (DocumentId, score) tuples
        """
        if self.bm25_index is None:
            return []

        results = self.bm25_index.search(query, top_k)
        return [(doc_id, score) for doc_id, score in results if score > min_score]

    def _reciprocal_rank_fusion(
        self,
        list_of_document_ids: list[list[tuple[DocumentId, float]]],
        list_of_weights: list[float],
        top_k: int,
    ) -> list[DocumentId]:
        """Combine multiple result lists using reciprocal rank fusion.

        Args:
            list_of_document_ids: List of result lists with scores
            list_of_weights: Weights for each list
            top_k: Number of results to return

        Returns:
            Combined list of document IDs
        """
        rrf_k = top_k * 2
        scores: dict[DocumentId, float] = {}

        for doc_ids, weight in zip(list_of_document_ids, list_of_weights):
            for index, (doc_id, _) in enumerate(doc_ids):
                score = 1.0 / (rrf_k + index + 1)
                scores[doc_id] = scores.get(doc_id, 0.0) + score * weight

        # Sort by score
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, _ in sorted_items[:top_k]]

    def export(self) -> dict:
        """Export RAG info as dictionary.

        Returns:
            Dictionary with RAG information
        """
        files = [
            {"path": f.path, "num_chunks": len(f.documents)}
            for f in self.data.files.values()
        ]
        return {
            "path": self.path,
            "embedding_model": self.data.embedding_model,
            "chunk_size": self.data.chunk_size,
            "chunk_overlap": self.data.chunk_overlap,
            "reranker_model": self.data.reranker_model,
            "top_k": self.data.top_k,
            "batch_size": self.data.batch_size,
            "document_paths": self.data.document_paths,
            "files": files,
        }


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
]
