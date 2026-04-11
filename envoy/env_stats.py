"""Statistics and summary reporting for .env variable sets."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvStats:
    total: int = 0
    empty_values: int = 0
    sensitive_keys: int = 0
    duplicate_values: int = 0
    longest_key: Optional[str] = None
    longest_value_key: Optional[str] = None
    prefixes: Dict[str, int] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"EnvStats(total={self.total}, empty={self.empty_values}, "
            f"sensitive={self.sensitive_keys}, duplicates={self.duplicate_values})"
        )


class EnvStatsCalculator:
    """Computes statistics over a dict of env variables."""

    # Common sensitive key substrings (aligned with secrets.py)
    _SENSITIVE_PATTERNS = (
        "password", "passwd", "secret", "token", "api_key",
        "apikey", "auth", "private", "credential",
    )

    def __init__(self, prefix_separator: str = "_") -> None:
        self._sep = prefix_separator

    def compute(self, vars: Dict[str, str]) -> EnvStats:
        if not vars:
            return EnvStats()

        total = len(vars)
        empty_values = sum(1 for v in vars.values() if v == "")
        sensitive_keys = sum(
            1 for k in vars
            if any(p in k.lower() for p in self._SENSITIVE_PATTERNS)
        )

        # Duplicate values (ignoring empty)
        value_counts: Dict[str, List[str]] = {}
        for k, v in vars.items():
            if v:
                value_counts.setdefault(v, []).append(k)
        duplicate_values = sum(
            len(keys) for keys in value_counts.values() if len(keys) > 1
        )

        longest_key = max(vars.keys(), key=len) if vars else None
        non_empty = {k: v for k, v in vars.items() if v}
        longest_value_key = max(non_empty, key=lambda k: len(non_empty[k])) if non_empty else None

        prefixes: Dict[str, int] = {}
        for k in vars:
            if self._sep in k:
                prefix = k.split(self._sep)[0]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1

        return EnvStats(
            total=total,
            empty_values=empty_values,
            sensitive_keys=sensitive_keys,
            duplicate_values=duplicate_values,
            longest_key=longest_key,
            longest_value_key=longest_value_key,
            prefixes=prefixes,
        )

    def summary_lines(self, stats: EnvStats) -> List[str]:
        lines = [
            f"Total variables   : {stats.total}",
            f"Empty values      : {stats.empty_values}",
            f"Sensitive keys    : {stats.sensitive_keys}",
            f"Duplicate values  : {stats.duplicate_values}",
        ]
        if stats.longest_key:
            lines.append(f"Longest key       : {stats.longest_key}")
        if stats.longest_value_key:
            lines.append(f"Longest value key : {stats.longest_value_key}")
        if stats.prefixes:
            top = sorted(stats.prefixes.items(), key=lambda x: -x[1])[:5]
            lines.append("Top prefixes      : " + ", ".join(f"{p}({c})" for p, c in top))
        return lines
