"""Extract a subset of variables from an env file by keys or pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ExtractResult:
    extracted: Dict[str, str] = field(default_factory=dict)
    missing_keys: List[str] = field(default_factory=list)
    matched_pattern: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ExtractResult(extracted={len(self.extracted)}, "
            f"missing={len(self.missing_keys)})"
        )

    @property
    def has_missing(self) -> bool:
        return bool(self.missing_keys)


class EnvExtractor:
    """Extract variables from a dict of env vars by explicit keys or regex pattern."""

    def __init__(self, ignore_missing: bool = False) -> None:
        self.ignore_missing = ignore_missing

    def extract_keys(
        self, vars: Dict[str, str], keys: List[str]
    ) -> ExtractResult:
        """Extract specific keys from vars."""
        extracted: Dict[str, str] = {}
        missing: List[str] = []

        for key in keys:
            if key in vars:
                extracted[key] = vars[key]
            else:
                if not self.ignore_missing:
                    missing.append(key)

        return ExtractResult(extracted=extracted, missing_keys=missing)

    def extract_pattern(
        self, vars: Dict[str, str], pattern: str
    ) -> ExtractResult:
        """Extract all keys matching a regex pattern."""
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern '{pattern}': {exc}") from exc

        extracted = {
            k: v for k, v in vars.items() if compiled.search(k)
        }
        return ExtractResult(extracted=extracted, matched_pattern=pattern)

    def extract_prefix(
        self, vars: Dict[str, str], prefix: str, strip_prefix: bool = False
    ) -> ExtractResult:
        """Extract all keys starting with a given prefix."""
        extracted: Dict[str, str] = {}
        for k, v in vars.items():
            if k.startswith(prefix):
                new_key = k[len(prefix):] if strip_prefix else k
                extracted[new_key] = v
        return ExtractResult(extracted=extracted)
