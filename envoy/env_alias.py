"""Alias management for env variable keys."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AliasEntry:
    canonical: str
    aliases: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"canonical": self.canonical, "aliases": list(self.aliases)}

    @classmethod
    def from_dict(cls, data: dict) -> "AliasEntry":
        return cls(canonical=data["canonical"], aliases=list(data.get("aliases", [])))

    def __repr__(self) -> str:
        return f"AliasEntry(canonical={self.canonical!r}, aliases={self.aliases!r})"


@dataclass
class AliasResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"AliasResult(resolved={len(self.resolved)}, "
            f"unresolved={len(self.unresolved)})"
        )


class EnvAliasManager:
    """Resolves and expands env variable aliases."""

    def __init__(self) -> None:
        self._entries: Dict[str, AliasEntry] = {}  # canonical -> entry
        self._alias_map: Dict[str, str] = {}       # alias -> canonical

    def register(self, canonical: str, aliases: List[str]) -> AliasEntry:
        entry = AliasEntry(canonical=canonical, aliases=aliases)
        self._entries[canonical] = entry
        for alias in aliases:
            self._alias_map[alias] = canonical
        return entry

    def resolve(self, key: str) -> Optional[str]:
        """Return canonical key for a given alias, or None if not found."""
        if key in self._entries:
            return key
        return self._alias_map.get(key)

    def expand(self, vars: Dict[str, str]) -> AliasResult:
        """Expand aliased keys in vars dict to their canonical forms."""
        resolved: Dict[str, str] = {}
        unresolved: List[str] = []
        for key, value in vars.items():
            canonical = self.resolve(key)
            if canonical:
                resolved[canonical] = value
            else:
                unresolved.append(key)
        return AliasResult(resolved=resolved, unresolved=unresolved)

    def list_entries(self) -> List[AliasEntry]:
        return list(self._entries.values())
