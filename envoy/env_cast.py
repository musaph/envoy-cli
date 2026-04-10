"""Type casting utilities for environment variable values."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CastResult:
    key: str
    raw: str
    casted: Any
    cast_type: str
    success: bool
    error: Optional[str] = None

    def __repr__(self) -> str:
        status = "ok" if self.success else f"error: {self.error}"
        return f"<CastResult {self.key}={self.casted!r} ({self.cast_type}) [{status}]>"


class EnvCaster:
    """Casts env var string values to appropriate Python types."""

    BOOL_TRUE = {"true", "1", "yes", "on"}
    BOOL_FALSE = {"false", "0", "no", "off"}

    def __init__(self, strict: bool = False):
        self.strict = strict

    def cast_value(self, key: str, value: str, hint: Optional[str] = None) -> CastResult:
        """Attempt to cast a single value, optionally using a type hint."""
        if hint:
            return self._cast_with_hint(key, value, hint)
        return self._infer_cast(key, value)

    def _cast_with_hint(self, key: str, value: str, hint: str) -> CastResult:
        casters = {
            "int": self._to_int,
            "float": self._to_float,
            "bool": self._to_bool,
            "str": lambda v: (v, None),
            "list": self._to_list,
        }
        fn = casters.get(hint)
        if fn is None:
            return CastResult(key, value, value, "str", True)
        result, error = fn(value)
        return CastResult(key, value, result if error is None else value, hint, error is None, error)

    def _infer_cast(self, key: str, value: str) -> CastResult:
        lower = value.strip().lower()
        if lower in self.BOOL_TRUE | self.BOOL_FALSE:
            result, err = self._to_bool(value)
            return CastResult(key, value, result if err is None else value, "bool", err is None, err)
        result, err = self._to_int(value)
        if err is None:
            return CastResult(key, value, result, "int", True)
        result, err = self._to_float(value)
        if err is None:
            return CastResult(key, value, result, "float", True)
        return CastResult(key, value, value, "str", True)

    def cast_all(self, vars_dict: Dict[str, str], hints: Optional[Dict[str, str]] = None) -> List[CastResult]:
        hints = hints or {}
        return [self.cast_value(k, v, hints.get(k)) for k, v in vars_dict.items()]

    def to_python_dict(self, vars_dict: Dict[str, str], hints: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return {r.key: r.casted for r in self.cast_all(vars_dict, hints)}

    @staticmethod
    def _to_int(value: str):
        try:
            return int(value), None
        except (ValueError, TypeError) as e:
            return None, str(e)

    @staticmethod
    def _to_float(value: str):
        try:
            return float(value), None
        except (ValueError, TypeError) as e:
            return None, str(e)

    def _to_bool(self, value: str):
        lower = value.strip().lower()
        if lower in self.BOOL_TRUE:
            return True, None
        if lower in self.BOOL_FALSE:
            return False, None
        return None, f"Cannot cast {value!r} to bool"

    @staticmethod
    def _to_list(value: str):
        items = [item.strip() for item in value.split(",") if item.strip()]
        return items, None
