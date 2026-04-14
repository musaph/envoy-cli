"""Coerce env var values to normalized string representations."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CoerceChange:
    key: str
    original: str
    coerced: str
    rule: str

    def __repr__(self) -> str:
        return f"CoerceChange(key={self.key!r}, rule={self.rule!r})"


@dataclass
class CoerceResult:
    changes: List[CoerceChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def __repr__(self) -> str:
        return (
            f"CoerceResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvCoercer:
    """Coerce env var values using named rules."""

    RULES = {
        "lowercase": str.lower,
        "uppercase": str.upper,
        "strip": str.strip,
        "bool_normalize": lambda v: (
            "true" if v.lower() in ("1", "yes", "true", "on") else
            "false" if v.lower() in ("0", "no", "false", "off") else v
        ),
        "strip_quotes": lambda v: v.strip("'\"")
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"') else v,
    }

    def __init__(self, rules: Optional[List[str]] = None) -> None:
        self.rules = rules or ["strip"]
        unknown = [r for r in self.rules if r not in self.RULES]
        if unknown:
            raise ValueError(f"Unknown coercion rules: {unknown}")

    def coerce(self, vars_: Dict[str, str]) -> CoerceResult:
        changes: List[CoerceChange] = []
        skipped: List[str] = []
        result: Dict[str, str] = {}

        for key, value in vars_.items():
            if not isinstance(value, str):
                skipped.append(key)
                result[key] = value
                continue
            current = value
            changed = False
            applied_rule = ""
            for rule_name in self.rules:
                fn = self.RULES[rule_name]
                new_val = fn(current)
                if new_val != current:
                    changed = True
                    applied_rule = rule_name
                    current = new_val
            if changed:
                changes.append(CoerceChange(
                    key=key, original=value, coerced=current, rule=applied_rule
                ))
            result[key] = current

        return CoerceResult(changes=changes, skipped=skipped)

    def coerce_value(self, value: str) -> str:
        current = value
        for rule_name in self.rules:
            current = self.RULES[rule_name](current)
        return current

    @classmethod
    def available_rules(cls) -> List[str]:
        """Return the list of available coercion rule names."""
        return list(cls.RULES.keys())
