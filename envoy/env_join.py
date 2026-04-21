"""Merge multiple env var dictionaries into one with configurable separator."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JoinChange:
    key: str
    sources: List[str]
    value: str

    def __repr__(self) -> str:
        return f"JoinChange(key={self.key!r}, sources={self.sources!r})"


@dataclass
class JoinResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[JoinChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"JoinResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)}, "
            f"total={len(self.vars)})"
        )


class EnvJoiner:
    """Join multiple env var sources into a single flat dict.

    Keys appearing in multiple sources are joined with *separator*.
    If *overwrite* is True the last source wins instead of joining.
    """

    def __init__(self, separator: str = ",", overwrite: bool = False) -> None:
        self.separator = separator
        self.overwrite = overwrite

    def join(
        self,
        sources: List[Dict[str, str]],
        source_names: Optional[List[str]] = None,
    ) -> JoinResult:
        if source_names is None:
            source_names = [f"source_{i}" for i in range(len(sources))]

        result: Dict[str, str] = {}
        origin: Dict[str, List[str]] = {}
        changes: List[JoinChange] = []
        skipped: List[str] = []

        for name, src in zip(source_names, sources):
            for key, value in src.items():
                if key not in result:
                    result[key] = value
                    origin[key] = [name]
                elif self.overwrite:
                    result[key] = value
                    origin[key].append(name)
                else:
                    result[key] = result[key] + self.separator + value
                    origin[key].append(name)

        for key, srcs in origin.items():
            if len(srcs) > 1:
                changes.append(JoinChange(key=key, sources=srcs, value=result[key]))

        return JoinResult(vars=result, changes=changes, skipped=skipped)
