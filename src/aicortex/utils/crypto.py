"""Cryptographic utilities.

Corresponds to src/utils/crypto.rs in the Rust implementation.
"""

import hashlib
import hmac
import base64
import urllib.parse
from typing import Union


def sha256(input: str) -> str:
    """Calculate SHA-256 hash of input string.

    Args:
        input: String to hash

    Returns:
        Hexadecimal SHA-256 hash
    """
    return hashlib.sha256(input.encode()).hexdigest()


def hmac_sha256(key: bytes, msg: str) -> bytes:
    """Calculate HMAC-SHA256.

    Args:
        key: HMAC key as bytes
        msg: Message to authenticate

    Returns:
        HMAC digest as bytes
    """
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def hex_encode(bytes_data: bytes) -> str:
    """Encode bytes as hexadecimal string.

    Args:
        bytes_data: Bytes to encode

    Returns:
        Lowercase hexadecimal string
    """
    return bytes_data.hex()


def encode_uri(uri: str) -> str:
    """URL-encode a URI path.

    Encodes each segment separately, preserving '/' separators.

    Args:
        uri: URI path to encode

    Returns:
        URL-encoded URI
    """
    parts = uri.split("/")
    encoded_parts = [urllib.parse.quote(part, safe="") for part in parts]
    return "/".join(encoded_parts)


def base64_encode(input: Union[bytes, str]) -> str:
    """Base64 encode input.

    Args:
        input: Bytes or string to encode

    Returns:
        Base64 encoded string
    """
    if isinstance(input, str):
        input = input.encode()
    return base64.b64encode(input).decode()


def base64_decode(input: Union[bytes, str]) -> bytes:
    """Base64 decode input.

    Args:
        input: Base64 encoded bytes or string

    Returns:
        Decoded bytes

    Raises:
        ValueError: If input is not valid Base64
    """
    if isinstance(input, str):
        input = input.encode()
    try:
        return base64.b64decode(input)
    except Exception as e:
        raise ValueError(f"Invalid Base64 input: {e}")


__all__ = [
    "sha256",
    "hmac_sha256",
    "hex_encode",
    "encode_uri",
    "base64_encode",
    "base64_decode",
]
