"""Key rotation support for envoy-cli."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from envoy.crypto import EnvoyCrypto


@dataclass
class RotationRecord:
    """Records a single key rotation event."""
    rotated_at: str
    keys_affected: int
    environment: str
    initiated_by: str = "cli"

    def to_dict(self) -> Dict:
        return {
            "rotated_at": self.rotated_at,
            "keys_affected": self.keys_affected,
            "environment": self.environment,
            "initiated_by": self.initiated_by,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RotationRecord":
        return cls(
            rotated_at=data["rotated_at"],
            keys_affected=data["keys_affected"],
            environment=data["environment"],
            initiated_by=data.get("initiated_by", "cli"),
        )


class KeyRotator:
    """Re-encrypts env vars from an old password to a new password."""

    def __init__(self, old_password: str, new_password: str):
        if not old_password or not new_password:
            raise ValueError("Passwords must be non-empty strings.")
        if old_password == new_password:
            raise ValueError("New password must differ from old password.")
        self._old_crypto = EnvoyCrypto(old_password)
        self._new_crypto = EnvoyCrypto(new_password)

    def rotate(self, encrypted_blob: str) -> str:
        """Decrypt with old password, re-encrypt with new password."""
        plaintext = self._old_crypto.decrypt(encrypted_blob)
        return self._new_crypto.encrypt(plaintext)

    def rotate_all(self, blobs: Dict[str, str]) -> Dict[str, str]:
        """Rotate a mapping of key -> encrypted_blob."""
        return {key: self.rotate(blob) for key, blob in blobs.items()}

    def build_record(
        self,
        environment: str,
        keys_affected: int,
        initiated_by: str = "cli",
    ) -> RotationRecord:
        return RotationRecord(
            rotated_at=datetime.utcnow().isoformat(),
            keys_affected=keys_affected,
            environment=environment,
            initiated_by=initiated_by,
        )
