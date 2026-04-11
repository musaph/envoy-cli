"""Namespace management for env vars — group vars by prefix (e.g. DB_, AWS_)."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NamespaceResult:
    namespace: str
    vars: Dict[str, str] = field(default_factory=dict)
    stripped: Dict[str, str] = field(default_factory=dict)  # prefix removed

    def __repr__(self) -> str:
        return f"<NamespaceResult ns={self.namespace!r} count={len(self.vars)}>"


class EnvNamespaceManager:
    """Splits env vars into namespaces based on key prefixes."""

    def __init__(self, separator: str = "_") -> None:
        self.separator = separator

    def extract(self, vars: Dict[str, str], namespace: str) -> NamespaceResult:
        """Return all vars whose keys start with `namespace` + separator."""
        prefix = namespace.rstrip(self.separator) + self.separator
        matched: Dict[str, str] = {}
        stripped: Dict[str, str] = {}
        for key, value in vars.items():
            if key.upper().startswith(prefix.upper()):
                matched[key] = value
                stripped_key = key[len(prefix):]
                stripped[stripped_key] = value
        return NamespaceResult(namespace=namespace, vars=matched, stripped=stripped)

    def list_namespaces(self, vars: Dict[str, str]) -> List[str]:
        """Return sorted list of unique top-level prefixes found in var keys."""
        namespaces: set = set()
        for key in vars:
            if self.separator in key:
                ns = key.split(self.separator)[0]
                namespaces.add(ns)
        return sorted(namespaces)

    def inject(self, vars: Dict[str, str], namespace: str,
               additions: Dict[str, str]) -> Dict[str, str]:
        """Return a new vars dict with `additions` prefixed under `namespace`."""
        prefix = namespace.rstrip(self.separator) + self.separator
        result = dict(vars)
        for key, value in additions.items():
            namespaced_key = prefix + key
            result[namespaced_key] = value
        return result

    def remove_namespace(self, vars: Dict[str, str], namespace: str) -> Dict[str, str]:
        """Return a new vars dict with all keys in `namespace` removed."""
        prefix = namespace.rstrip(self.separator) + self.separator
        return {k: v for k, v in vars.items()
                if not k.upper().startswith(prefix.upper())}
