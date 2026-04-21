from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EscapeChange:
    key: str
    original: str
    escaped: str

    def __repr__(self) -> str:
        return f"EscapeChange(key={self.key!r}, original={self.original!r}, escaped={self.escaped!r})"


@dataclass
class EscapeResult:
    changes: List[EscapeChange] = field(default_factory=list)
    vars: Dict[str, str] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"EscapeResult(changes={len(self.changes)}, vars={len(self.vars)})"


class EnvEscaper:
    """Escapes special characters in .env variable values."""

    # Characters that need escaping in .env values
    _ESCAPE_MAP = {
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
        "\\": "\\\\",
    }

    def __init__(self, keys: Optional[List[str]] = None, unescape: bool = False):
        """
        Args:
            keys: If provided, only escape values for these keys. Otherwise escape all.
            unescape: If True, reverse the escaping (unescape).
        """
        self.keys = set(keys) if keys else None
        self.unescape = unescape

    def _escape_value(self, value: str) -> str:
        for char, escaped in self._ESCAPE_MAP.items():
            value = value.replace(char, escaped)
        return value

    def _unescape_value(self, value: str) -> str:
        for char, escaped in self._ESCAPE_MAP.items():
            value = value.replace(escaped, char)
        return value

    def process(self, vars: Dict[str, str]) -> EscapeResult:
        result_vars = dict(vars)
        changes: List[EscapeChange] = []

        for key, value in vars.items():
            if self.keys is not None and key not in self.keys:
                continue

            if self.unescape:
                new_value = self._unescape_value(value)
            else:
                new_value = self._escape_value(value)

            if new_value != value:
                changes.append(EscapeChange(key=key, original=value, escaped=new_value))
                result_vars[key] = new_value

        return EscapeResult(changes=changes, vars=result_vars)
