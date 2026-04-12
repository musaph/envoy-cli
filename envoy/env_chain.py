"""Chain multiple .env files with override precedence."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ChainEntry:
    source: str
    key: str
    value: str
    overridden_by: Optional[str] = None

    def __repr__(self) -> str:
        tag = f" -> overridden by {self.overridden_by}" if self.overridden_by else ""
        return f"ChainEntry({self.source}:{self.key}{tag})"


@dataclass
class ChainResult:
    merged: Dict[str, str] = field(default_factory=dict)
    entries: List[ChainEntry] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ChainResult(sources={len(self.sources)}, "
            f"keys={len(self.merged)}, "
            f"overrides={sum(1 for e in self.entries if e.overridden_by)})"
        )

    @property
    def overridden_entries(self) -> List[ChainEntry]:
        return [e for e in self.entries if e.overridden_by]


class EnvChainer:
    """Merges multiple env var dicts in order; later sources override earlier ones."""

    def chain(self, sources: List[Tuple[str, Dict[str, str]]]) -> ChainResult:
        """Chain sources in order. Each (name, vars) pair; last writer wins."""
        merged: Dict[str, str] = {}
        # key -> source name that currently holds the winning value
        winner: Dict[str, str] = {}
        all_entries: List[ChainEntry] = []

        for source_name, vars_dict in sources:
            for key, value in vars_dict.items():
                if key in winner:
                    # Mark the previous entry as overridden
                    for entry in reversed(all_entries):
                        if entry.key == key and entry.source == winner[key] and entry.overridden_by is None:
                            entry.overridden_by = source_name
                            break
                all_entries.append(ChainEntry(source=source_name, key=key, value=value))
                merged[key] = value
                winner[key] = source_name

        return ChainResult(
            merged=merged,
            entries=all_entries,
            sources=[name for name, _ in sources],
        )
