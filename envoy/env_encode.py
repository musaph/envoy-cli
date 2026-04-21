from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import urllib.parse
import base64 as _b64


@dataclass
class EncodeChange:
    key: str
    original: str
    encoded: str
    encoding: str

    def __repr__(self) -> str:
        return f"EncodeChange(key={self.key!r}, encoding={self.encoding!r})"


@dataclass
class EncodeResult:
    changes: List[EncodeChange] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"EncodeResult(changes={len(self.changes)}, errors={len(self.errors)})"
        )


SUPPORTED_ENCODINGS = ("url", "base64", "hex")


class EnvEncoder:
    def __init__(
        self,
        encoding: str = "url",
        keys: Optional[List[str]] = None,
    ) -> None:
        if encoding not in SUPPORTED_ENCODINGS:
            raise ValueError(
                f"Unsupported encoding {encoding!r}. Choose from {SUPPORTED_ENCODINGS}."
            )
        self.encoding = encoding
        self.keys = set(keys) if keys else None

    def _encode_value(self, value: str) -> str:
        if self.encoding == "url":
            return urllib.parse.quote(value, safe="")
        if self.encoding == "base64":
            return _b64.b64encode(value.encode()).decode()
        if self.encoding == "hex":
            return value.encode().hex()
        raise ValueError(f"Unknown encoding: {self.encoding}")

    def encode(self, vars: Dict[str, str]) -> EncodeResult:
        result = EncodeResult()
        for key, value in vars.items():
            if self.keys is not None and key not in self.keys:
                continue
            try:
                encoded = self._encode_value(value)
                if encoded != value:
                    result.changes.append(
                        EncodeChange(
                            key=key,
                            original=value,
                            encoded=encoded,
                            encoding=self.encoding,
                        )
                    )
            except Exception as exc:  # pragma: no cover
                result.errors.append(f"{key}: {exc}")
        return result

    def apply(self, vars: Dict[str, str]) -> Dict[str, str]:
        result = self.encode(vars)
        out = dict(vars)
        for change in result.changes:
            out[change.key] = change.encoded
        return out
