"""Compare two sets of env vars and produce a structured report."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CompareEntry:
    key: str
    local_value: Optional[str]
    remote_value: Optional[str]
    status: str  # 'match', 'differ', 'local_only', 'remote_only'

    def __repr__(self) -> str:
        return f"CompareEntry(key={self.key!r}, status={self.status!r})"


@dataclass
class CompareReport:
    entries: List[CompareEntry] = field(default_factory=list)

    @property
    def matches(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "match"]

    @property
    def differences(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "differ"]

    @property
    def local_only(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "local_only"]

    @property
    def remote_only(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "remote_only"]

    @property
    def is_identical(self) -> bool:
        return len(self.differences) == 0 and len(self.local_only) == 0 and len(self.remote_only) == 0

    def __repr__(self) -> str:
        return (
            f"CompareReport(matches={len(self.matches)}, differ={len(self.differences)}, "
            f"local_only={len(self.local_only)}, remote_only={len(self.remote_only)})"
        )


class EnvComparer:
    """Compare two env var dicts and return a structured CompareReport."""

    def compare(
        self,
        local: Dict[str, str],
        remote: Dict[str, str],
    ) -> CompareReport:
        entries: List[CompareEntry] = []
        all_keys = set(local) | set(remote)

        for key in sorted(all_keys):
            in_local = key in local
            in_remote = key in remote

            if in_local and in_remote:
                status = "match" if local[key] == remote[key] else "differ"
                entries.append(CompareEntry(key, local[key], remote[key], status))
            elif in_local:
                entries.append(CompareEntry(key, local[key], None, "local_only"))
            else:
                entries.append(CompareEntry(key, None, remote[key], "remote_only"))

        return CompareReport(entries=entries)
