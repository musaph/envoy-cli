"""Tests for envoy.rotate."""
import pytest
from envoy.crypto import EnvoyCrypto
from envoy.rotate import KeyRotator, RotationRecord


OLD_PASS = "old-secret-password"
NEW_PASS = "new-secret-password"


@pytest.fixture
def rotator():
    return KeyRotator(OLD_PASS, NEW_PASS)


def _encrypt(password: str, plaintext: str) -> str:
    return EnvoyCrypto(password).encrypt(plaintext)


def _decrypt(password: str, blob: str) -> str:
    return EnvoyCrypto(password).decrypt(blob)


class TestKeyRotator:
    def test_rotate_single_blob(self, rotator):
        blob = _encrypt(OLD_PASS, "secret_value")
        new_blob = rotator.rotate(blob)
        assert _decrypt(NEW_PASS, new_blob) == "secret_value"

    def test_rotate_all_blobs(self, rotator):
        blobs = {
            "DB_PASS": _encrypt(OLD_PASS, "db123"),
            "API_KEY": _encrypt(OLD_PASS, "key-abc"),
        }
        rotated = rotator.rotate_all(blobs)
        assert _decrypt(NEW_PASS, rotated["DB_PASS"]) == "db123"
        assert _decrypt(NEW_PASS, rotated["API_KEY"]) == "key-abc"

    def test_old_password_cannot_decrypt_after_rotation(self, rotator):
        blob = _encrypt(OLD_PASS, "value")
        new_blob = rotator.rotate(blob)
        with pytest.raises(Exception):
            _decrypt(OLD_PASS, new_blob)

    def test_same_password_raises(self):
        with pytest.raises(ValueError, match="differ"):
            KeyRotator("same", "same")

    def test_empty_old_password_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            KeyRotator("", "new")

    def test_empty_new_password_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            KeyRotator("old", "")

    def test_build_record_fields(self, rotator):
        record = rotator.build_record(environment="staging", keys_affected=5)
        assert record.environment == "staging"
        assert record.keys_affected == 5
        assert record.initiated_by == "cli"
        assert "T" in record.rotated_at  # ISO format contains T

    def test_rotate_all_empty_dict(self, rotator):
        assert rotator.rotate_all({}) == {}


class TestRotationRecord:
    def test_to_dict_roundtrip(self):
        rec = RotationRecord(
            rotated_at="2024-01-01T00:00:00",
            keys_affected=3,
            environment="production",
            initiated_by="admin",
        )
        d = rec.to_dict()
        restored = RotationRecord.from_dict(d)
        assert restored.rotated_at == rec.rotated_at
        assert restored.keys_affected == rec.keys_affected
        assert restored.environment == rec.environment
        assert restored.initiated_by == rec.initiated_by

    def test_from_dict_default_initiated_by(self):
        data = {"rotated_at": "2024-01-01T00:00:00", "keys_affected": 1, "environment": "dev"}
        rec = RotationRecord.from_dict(data)
        assert rec.initiated_by == "cli"
