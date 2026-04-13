"""Generate .env files from a set of field definitions with optional defaults and types."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import secrets
import string


@dataclass
class GenerateField:
    key: str
    default: Optional[str] = None
    auto: Optional[str] = None  # 'uuid', 'secret', 'token'
    required: bool = False

    def __repr__(self) -> str:
        return f"GenerateField(key={self.key!r}, auto={self.auto!r}, required={self.required})"


@dataclass
class GenerateResult:
    generated: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __repr__(self) -> str:
        return (
            f"GenerateResult(generated={len(self.generated)}, "
            f"skipped={len(self.skipped)}, errors={len(self.errors)})"
        )


class EnvGenerator:
    _AUTO_TYPES = ("uuid", "secret", "token")

    def __init__(self, length: int = 32):
        self.length = length

    def _generate_value(self, auto: str) -> str:
        if auto == "uuid":
            import uuid
            return str(uuid.uuid4())
        elif auto in ("secret", "token"):
            alphabet = string.ascii_letters + string.digits
            return "".join(secrets.choice(alphabet) for _ in range(self.length))
        raise ValueError(f"Unknown auto type: {auto!r}")

    def generate(self, fields: List[GenerateField], overrides: Optional[Dict[str, str]] = None) -> GenerateResult:
        overrides = overrides or {}
        result = GenerateResult()
        for f in fields:
            if f.key in overrides:
                result.generated[f.key] = overrides[f.key]
            elif f.auto and f.auto in self._AUTO_TYPES:
                result.generated[f.key] = self._generate_value(f.auto)
            elif f.default is not None:
                result.generated[f.key] = f.default
            elif f.required:
                result.errors.append(f"Required field {f.key!r} has no value or default")
            else:
                result.skipped.append(f.key)
        return result
