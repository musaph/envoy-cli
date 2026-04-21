from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MaskKeyChange:
    key: str
    original_key: str
    masked_key: str

    def __repr__(self) -> str:
        return f"MaskKeyChange(key={self.key!r}, masked_key={self.masked_key!r})"


@dataclass
class MaskKeyResult:
    changes: List[MaskKeyChange] = field(default_factory=list)
    original: Dict[str, str] = field(default_factory=dict)
    masked: Dict[str, str] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"MaskKeyResult(changes={len(self.changes)}, has_changes={self.has_changes()})"


class EnvKeyMasker:
    """Masks (obfuscates) environment variable keys by replacing characters."""

    DEFAULT_MASK_CHAR = "*"
    DEFAULT_VISIBLE_CHARS = 2

    def __init__(
        self,
        mask_char: str = DEFAULT_MASK_CHAR,
        visible_chars: int = DEFAULT_VISIBLE_CHARS,
        keys: Optional[List[str]] = None,
    ):
        self.mask_char = mask_char
        self.visible_chars = max(0, visible_chars)
        self.keys = set(keys) if keys else None

    def _mask_key(self, key: str) -> str:
        if len(key) <= self.visible_chars:
            return key
        visible = key[: self.visible_chars]
        masked_part = self.mask_char * (len(key) - self.visible_chars)
        return visible + masked_part

    def mask(self, vars_: Dict[str, str]) -> MaskKeyResult:
        changes: List[MaskKeyChange] = []
        masked: Dict[str, str] = {}

        for key, value in vars_.items():
            should_mask = self.keys is None or key in self.keys
            if should_mask:
                new_key = self._mask_key(key)
                if new_key != key:
                    changes.append(MaskKeyChange(key=key, original_key=key, masked_key=new_key))
                masked[new_key] = value
            else:
                masked[key] = value

        return MaskKeyResult(changes=changes, original=dict(vars_), masked=masked)
