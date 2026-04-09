"""Secret scanning and masking utilities for envoy-cli."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Patterns that suggest a value is sensitive
SECRET_KEY_PATTERNS = [
    re.compile(r"(password|passwd|pwd)", re.IGNORECASE),
    re.compile(r"(secret|token|api_key|apikey)", re.IGNORECASE),
    re.compile(r"(private_key|priv_key|pkey)", re.IGNORECASE),
    re.compile(r"(access_key|auth_key|auth_token)", re.IGNORECASE),
    re.compile(r"(credentials|credential|cred)", re.IGNORECASE),
]

SECRET_VALUE_PATTERNS = [
    re.compile(r"^[A-Za-z0-9+/]{32,}={0,2}$"),  # base64-like
    re.compile(r"^[0-9a-fA-F]{32,}$"),            # hex string
    re.compile(r"^sk-[A-Za-z0-9]{20,}$"),         # OpenAI-style key
    re.compile(r"^ghp_[A-Za-z0-9]{36}$"),         # GitHub token
    re.compile(r"^xox[baprs]-[0-9A-Za-z\-]{10,}$"),  # Slack token
]

MASK_PLACEHOLDER = "***MASKED***"


@dataclass
class SecretMatch:
    key: str
    reason: str
    value_preview: str = ""

    def __repr__(self) -> str:
        return f"SecretMatch(key={self.key!r}, reason={self.reason!r})"


class SecretScanner:
    """Scans env variable keys/values for potentially sensitive data."""

    def __init__(self, extra_key_patterns: Optional[List[str]] = None):
        self._key_patterns = list(SECRET_KEY_PATTERNS)
        if extra_key_patterns:
            for p in extra_key_patterns:
                self._key_patterns.append(re.compile(p, re.IGNORECASE))

    def is_sensitive_key(self, key: str) -> bool:
        return any(p.search(key) for p in self._key_patterns)

    def is_sensitive_value(self, value: str) -> bool:
        return any(p.match(value) for p in SECRET_VALUE_PATTERNS)

    def scan(self, variables: dict) -> List[SecretMatch]:
        """Return a list of SecretMatch for variables deemed sensitive."""
        matches: List[SecretMatch] = []
        for key, value in variables.items():
            if self.is_sensitive_key(key):
                preview = (value[:4] + "...") if len(value) > 4 else "..."
                matches.append(SecretMatch(key=key, reason="key name pattern", value_preview=preview))
            elif self.is_sensitive_value(str(value)):
                preview = (value[:4] + "...") if len(value) > 4 else "..."
                matches.append(SecretMatch(key=key, reason="value entropy pattern", value_preview=preview))
        return matches

    def mask(self, variables: dict) -> dict:
        """Return a copy of variables with sensitive values replaced."""
        result = {}
        for key, value in variables.items():
            if self.is_sensitive_key(key) or self.is_sensitive_value(str(value)):
                result[key] = MASK_PLACEHOLDER
            else:
                result[key] = value
        return result
