"""Field-level encryption for individual .env values."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envoy.crypto import EnvoyCrypto


@dataclass
class FieldEncryptResult:
    encrypted: Dict[str, str]
    skipped: List[str]
    errors: Dict[str, str]

    def __repr__(self) -> str:
        return (
            f"FieldEncryptResult(encrypted={len(self.encrypted)}, "
            f"skipped={len(self.skipped)}, errors={len(self.errors)})"
        )

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


ENCRYPTED_PREFIX = "enc:"


class EnvFieldEncryptor:
    """Encrypts or decrypts individual fields in a vars dict."""

    def __init__(self, password: str, salt: Optional[bytes] = None) -> None:
        self._password = password
        self._salt = salt
        self._crypto = EnvoyCrypto(password, salt)

    def encrypt_fields(
        self, vars: Dict[str, str], keys: Optional[List[str]] = None
    ) -> FieldEncryptResult:
        """Encrypt specific keys (or all if keys is None)."""
        target_keys = keys if keys is not None else list(vars.keys())
        encrypted: Dict[str, str] = {}
        skipped: List[str] = []
        errors: Dict[str, str] = {}

        for k, v in vars.items():
            if k not in target_keys:
                encrypted[k] = v
                continue
            if v.startswith(ENCRYPTED_PREFIX):
                skipped.append(k)
                encrypted[k] = v
                continue
            try:
                blob = self._crypto.encrypt(v)
                encrypted[k] = f"{ENCRYPTED_PREFIX}{blob}"
            except Exception as exc:
                errors[k] = str(exc)
                encrypted[k] = v

        return FieldEncryptResult(encrypted=encrypted, skipped=skipped, errors=errors)

    def decrypt_fields(
        self, vars: Dict[str, str], keys: Optional[List[str]] = None
    ) -> FieldEncryptResult:
        """Decrypt specific keys (or all encrypted fields if keys is None)."""
        target_keys = set(keys) if keys is not None else None
        decrypted: Dict[str, str] = {}
        skipped: List[str] = []
        errors: Dict[str, str] = {}

        for k, v in vars.items():
            if target_keys is not None and k not in target_keys:
                decrypted[k] = v
                continue
            if not v.startswith(ENCRYPTED_PREFIX):
                skipped.append(k)
                decrypted[k] = v
                continue
            blob = v[len(ENCRYPTED_PREFIX):]
            try:
                decrypted[k] = self._crypto.decrypt(blob)
            except Exception as exc:
                errors[k] = str(exc)
                decrypted[k] = v

        return FieldEncryptResult(encrypted=decrypted, skipped=skipped, errors=errors)

    def encrypted_keys(self, vars: Dict[str, str]) -> List[str]:
        """Return a list of keys whose values are currently encrypted."""
        return [k for k, v in vars.items() if self.is_encrypted(v)]

    @staticmethod
    def is_encrypted(value: str) -> bool:
        return value.startswith(ENCRYPTED_PREFIX)
