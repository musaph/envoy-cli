from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TrimKeyChange:
    original: str
    trimmed: str

    def __repr__(self) -> str:
        return f"TrimKeyChange({self.original!r} -> {self.trimmed!r})"


@dataclass
class TrimKeyResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[TrimKeyChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.original for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"TrimKeyResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvKeyTrimmer:
    """Strips leading/trailing whitespace from environment variable keys."""

    def __init__(self, chars: str = None, overwrite: bool = False):
        self._chars = chars
        self._overwrite = overwrite

    def trim(self, vars: Dict[str, str]) -> TrimKeyResult:
        result_vars: Dict[str, str] = {}
        changes: List[TrimKeyChange] = []
        skipped: List[str] = []

        for key, value in vars.items():
            trimmed = key.strip(self._chars) if self._chars else key.strip()

            if trimmed == key:
                result_vars[key] = value
                continue

            if not trimmed:
                skipped.append(key)
                result_vars[key] = value
                continue

            if trimmed in vars and not self._overwrite:
                skipped.append(key)
                result_vars[key] = value
                continue

            changes.append(TrimKeyChange(original=key, trimmed=trimmed))
            result_vars[trimmed] = value

        return TrimKeyResult(vars=result_vars, changes=changes, skipped=skipped)
