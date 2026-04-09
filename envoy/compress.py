"""Compression utilities for env var payloads before encryption."""

import zlib
import base64
from dataclasses import dataclass
from typing import Dict


@dataclass
class CompressResult:
    original_size: int
    compressed_size: int
    ratio: float

    def __repr__(self) -> str:
        return (
            f"CompressResult(original={self.original_size}B, "
            f"compressed={self.compressed_size}B, ratio={self.ratio:.2f})"
        )


class EnvCompressor:
    """Compress and decompress env var payloads using zlib."""

    DEFAULT_LEVEL = 6  # zlib compression level (0-9)

    def __init__(self, level: int = DEFAULT_LEVEL) -> None:
        if not 0 <= level <= 9:
            raise ValueError(f"Compression level must be 0-9, got {level}")
        self.level = level

    def compress(self, data: bytes) -> bytes:
        """Compress raw bytes and return base64-encoded compressed bytes."""
        compressed = zlib.compress(data, self.level)
        return base64.b64encode(compressed)

    def decompress(self, data: bytes) -> bytes:
        """Decode base64 and decompress bytes back to original."""
        raw = base64.b64decode(data)
        return zlib.decompress(raw)

    def compress_vars(self, vars_dict: Dict[str, str]) -> bytes:
        """Serialize and compress a vars dictionary."""
        lines = "\n".join(f"{k}={v}" for k, v in sorted(vars_dict.items()))
        return self.compress(lines.encode("utf-8"))

    def decompress_vars(self, data: bytes) -> Dict[str, str]:
        """Decompress and deserialize bytes back to a vars dictionary."""
        raw = self.decompress(data)
        result: Dict[str, str] = {}
        for line in raw.decode("utf-8").splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
        return result

    def stats(self, original: bytes, compressed: bytes) -> CompressResult:
        """Return compression statistics for a given input/output pair."""
        orig_size = len(original)
        comp_size = len(compressed)
        ratio = comp_size / orig_size if orig_size > 0 else 1Result(
            original_size=orig_size,
            compressed_size=comp_size,
            ratio=ratio,
        )
