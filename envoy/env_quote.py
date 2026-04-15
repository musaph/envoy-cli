"""Quoting and unquoting of .env variable values."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class QuoteChange:
    key: str
    old_value: str
    new_value: str
    action: str  # 'quoted' | 'unquoted' | 'requoted'

    def __repr__(self) -> str:
        return f"QuoteChange(key={self.key!r}, action={self.action!r})"


@dataclass
class QuoteResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[QuoteChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"QuoteResult(total={len(self.vars)}, changes={len(self.changes)})"
        )


class EnvQuoter:
    """Add, remove, or normalise quotes around .env values."""

    QUOTE_CHAR = '"'

    def __init__(self, style: str = "double", only_if_needed: bool = False):
        """
        Args:
            style: 'double' or 'single' — which quote character to use.
            only_if_needed: when True, only quote values that contain
                            spaces, special characters, or are empty.
        """
        if style not in ("double", "single"):
            raise ValueError("style must be 'double' or 'single'")
        self._q = '"' if style == "double" else "'"
        self._only_if_needed = only_if_needed

    # ------------------------------------------------------------------
    def _needs_quoting(self, value: str) -> bool:
        if value == "":
            return True
        specials = " \t#$\\'\""
        return any(ch in value for ch in specials)

    def _strip_quotes(self, value: str) -> str:
        for q in ('"', "'"):
            if len(value) >= 2 and value[0] == q and value[-1] == q:
                return value[1:-1]
        return value

    def _is_quoted(self, value: str) -> bool:
        for q in ('"', "'"):
            if len(value) >= 2 and value[0] == q and value[-1] == q:
                return True
        return False

    # ------------------------------------------------------------------
    def quote(self, vars: Dict[str, str]) -> QuoteResult:
        """Ensure values are wrapped with the configured quote character."""
        result_vars: Dict[str, str] = {}
        changes: List[QuoteChange] = []

        for key, value in vars.items():
            raw = self._strip_quotes(value)
            if self._only_if_needed and not self._needs_quoting(raw):
                result_vars[key] = value
                continue
            new_value = f"{self._q}{raw}{self._q}"
            if new_value != value:
                action = "requoted" if self._is_quoted(value) else "quoted"
                changes.append(QuoteChange(key, value, new_value, action))
            result_vars[key] = new_value

        return QuoteResult(vars=result_vars, changes=changes)

    def unquote(self, vars: Dict[str, str]) -> QuoteResult:
        """Strip any surrounding quotes from values."""
        result_vars: Dict[str, str] = {}
        changes: List[QuoteChange] = []

        for key, value in vars.items():
            new_value = self._strip_quotes(value)
            if new_value != value:
                changes.append(QuoteChange(key, value, new_value, "unquoted"))
            result_vars[key] = new_value

        return QuoteResult(vars=result_vars, changes=changes)
