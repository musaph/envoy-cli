"""Sensitive key detection and classification for env vars."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SensitiveEntry:
    key: str
    value: str
    category: str
    confidence: str  # 'high' | 'medium' | 'low'

    def __repr__(self) -> str:
        return f"SensitiveEntry(key={self.key!r}, category={self.category!r}, confidence={self.confidence!r})"


@dataclass
class SensitiveResult:
    entries: List[SensitiveEntry] = field(default_factory=list)
    scanned: int = 0

    @property
    def found(self) -> bool:
        return len(self.entries) > 0

    @property
    def high_confidence(self) -> List[SensitiveEntry]:
        return [e for e in self.entries if e.confidence == "high"]

    def __repr__(self) -> str:
        return f"SensitiveResult(scanned={self.scanned}, found={len(self.entries)})"


_CATEGORIES: Dict[str, List[str]] = {
    "credential": ["password", "passwd", "secret", "credentials"],
    "token": ["token", "api_key", "apikey", "access_key", "auth_key"],
    "certificate": ["cert", "certificate", "private_key", "pem"],
    "database": ["db_pass", "database_password", "db_password", "db_url"],
    "connection": ["dsn", "connection_string", "conn_str"],
}

_HIGH_VALUE_PATTERN = re.compile(
    r"(password|secret|private_key|api_key|token|credential)", re.IGNORECASE
)
_MEDIUM_VALUE_PATTERN = re.compile(
    r"(key|auth|cert|pass|dsn|conn)", re.IGNORECASE
)


class EnvSensitiveClassifier:
    def __init__(self, extra_patterns: Optional[Dict[str, List[str]]] = None):
        self._categories = dict(_CATEGORIES)
        if extra_patterns:
            for cat, patterns in extra_patterns.items():
                self._categories.setdefault(cat, []).extend(patterns)

    def _classify(self, key: str) -> Optional[tuple]:
        lower = key.lower()
        for category, patterns in self._categories.items():
            for pattern in patterns:
                if pattern in lower:
                    confidence = "high" if _HIGH_VALUE_PATTERN.search(key) else "medium"
                    return category, confidence
        if _MEDIUM_VALUE_PATTERN.search(key):
            return "generic", "low"
        return None

    def classify(self, vars: Dict[str, str]) -> SensitiveResult:
        entries = []
        for key, value in vars.items():
            result = self._classify(key)
            if result:
                category, confidence = result
                entries.append(SensitiveEntry(key=key, value=value, category=category, confidence=confidence))
        return SensitiveResult(entries=entries, scanned=len(vars))
