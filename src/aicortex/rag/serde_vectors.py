"""Vector serialization and deserialization for RAG.

Corresponds to src/rag/serde_vectors.rs in the Rust implementation.
"""

import base64
import struct
from typing import Any
from collections import OrderedDict


class DocumentId:
    """Unique identifier for a document chunk.

    Combines file_index and document_index into a single 64-bit value.
    """

    def __init__(self, file_index: int, document_index: int):
        """Create a DocumentId.

        Args:
            file_index: Index of the file
            document_index: Index of the document within the file
        """
        self.file_index = file_index
        self.document_index = document_index

    @property
    def value(self) -> int:
        """Get the combined value."""
        return (self.file_index << 32) | self.document_index

    @classmethod
    def from_value(cls, value: int) -> "DocumentId":
        """Create DocumentId from combined value.

        Args:
            value: Combined 64-bit value

        Returns:
            DocumentId instance
        """
        low_mask = (1 << 32) - 1
        document_index = value & low_mask
        file_index = value >> 32
        return cls(file_index, document_index)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.file_index}-{self.document_index}"

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, DocumentId):
            return False
        return (
            self.file_index == other.file_index
            and self.document_index == other.document_index
        )

    def __hash__(self) -> int:
        """Hash for use in dicts/sets."""
        return hash((self.file_index, self.document_index))

    def __lt__(self, other: "DocumentId") -> bool:
        """Less than comparison."""
        if self.file_index != other.file_index:
            return self.file_index < other.file_index
        return self.document_index < other.document_index

    def __le__(self, other: "DocumentId") -> bool:
        """Less than or equal comparison."""
        return self == other or self < other

    def __gt__(self, other: "DocumentId") -> bool:
        """Greater than comparison."""
        return not self <= other

    def __ge__(self, other: "DocumentId") -> bool:
        """Greater than or equal comparison."""
        return not self < other

    def split(self) -> tuple[int, int]:
        """Split into file_index and document_index.

        Returns:
            Tuple of (file_index, document_index)
        """
        return self.file_index, self.document_index


def serialize_vectors(vectors: "OrderedDict[DocumentId, list[float]]") -> dict[str, str]:
    """Serialize vectors to base64-encoded strings.

    Args:
        vectors: Dictionary mapping DocumentId to float vectors

    Returns:
        Dictionary with string keys and base64-encoded values
    """
    encoded_map: dict[str, str] = {}

    for doc_id, vec in vectors.items():
        # Convert floats to bytes
        byte_array = struct.pack(f"{len(vec)}f", *vec)
        # Encode to base64
        base64_str = base64.b64encode(byte_array).decode("ascii")
        key = str(doc_id)
        encoded_map[key] = base64_str

    return encoded_map


def deserialize_vectors(encoded_map: dict[str, str]) -> "OrderedDict[DocumentId, list[float]]":
    """Deserialize vectors from base64-encoded strings.

    Args:
        encoded_map: Dictionary with string keys and base64-encoded values

    Returns:
        Dictionary mapping DocumentId to float vectors
    """
    decoded_map: OrderedDict[DocumentId, list[float]] = OrderedDict()

    for key, base64_str in encoded_map.items():
        # Parse key
        try:
            parts = key.split("-")
            if len(parts) != 2:
                raise ValueError(f"Invalid key format: {key}")

            file_index = int(parts[0])
            document_index = int(parts[1])
            doc_id = DocumentId(file_index, document_index)

            # Decode base64
            decoded_data = base64.b64decode(base64_str)

            # Convert bytes to floats
            num_floats = len(decoded_data) // 4
            if len(decoded_data) % 4 != 0:
                raise ValueError(f"Invalid vector data for key '{key}'")

            vec = list(struct.unpack(f"{num_floats}f", decoded_data))
            decoded_map[doc_id] = vec

        except (ValueError, struct.error) as e:
            raise ValueError(f"Failed to deserialize vector for key '{key}': {e}")

    return decoded_map


__all__ = ["DocumentId", "serialize_vectors", "deserialize_vectors"]
