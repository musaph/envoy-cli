"""Annotation support for .env variables — attach inline comments/metadata."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Annotation:
    key: str
    comment: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"key": self.key, "comment": self.comment, "tags": list(self.tags)}

    @classmethod
    def from_dict(cls, data: dict) -> "Annotation":
        return cls(
            key=data["key"],
            comment=data.get("comment", ""),
            tags=list(data.get("tags", [])),
        )

    def __repr__(self) -> str:
        return f"Annotation(key={self.key!r}, comment={self.comment!r}, tags={self.tags})"


@dataclass
class AnnotateResult:
    annotated: Dict[str, Annotation] = field(default_factory=dict)
    unknown_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"AnnotateResult(annotated={len(self.annotated)}, "
            f"unknown_keys={self.unknown_keys})"
        )


class EnvAnnotator:
    """Attach and retrieve annotations for environment variable keys."""

    def __init__(self) -> None:
        self._annotations: Dict[str, Annotation] = {}

    def annotate(self, key: str, comment: str, tags: Optional[List[str]] = None) -> Annotation:
        """Add or update an annotation for a key."""
        ann = Annotation(key=key, comment=comment, tags=list(tags or []))
        self._annotations[key] = ann
        return ann

    def apply(self, vars: Dict[str, str]) -> AnnotateResult:
        """Return annotations that match keys present in vars."""
        annotated = {k: v for k, v in self._annotations.items() if k in vars}
        unknown = [k for k in self._annotations if k not in vars]
        return AnnotateResult(annotated=annotated, unknown_keys=unknown)

    def get(self, key: str) -> Optional[Annotation]:
        return self._annotations.get(key)

    def remove(self, key: str) -> bool:
        if key in self._annotations:
            del self._annotations[key]
            return True
        return False

    def all_annotations(self) -> Dict[str, Annotation]:
        return dict(self._annotations)
