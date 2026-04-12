"""Tests for field-level encryption."""
import pytest
from envoy.env_encrypt_field import EnvFieldEncryptor, FieldEncryptResult, ENCRYPTED_PREFIX


@pytest.fixture
def encryptor():
    return EnvFieldEncryptor(password="test-password")


class TestFieldEncryptResult:
    def test_repr(self):
        r = FieldEncryptResult(encrypted={"A": "1"}, skipped=["B"], errors={})
        assert "FieldEncryptResult" in repr(r)
        assert "skipped=1" in repr(r)

    def test_has_errors_false_when_empty(self):
        r = FieldEncryptResult(encrypted={}, skipped=[], errors={})
        assert r.has_errors is False

    def test_has_errors_true_when_populated(self):
        r = FieldEncryptResult(encrypted={}, skipped=[], errors={"K": "bad"})
        assert r.has_errors is True


class TestEnvFieldEncryptor:
    def test_encrypt_all_fields(self, encryptor):
        vars_ = {"DB_PASS": "secret", "APP_NAME": "myapp"}
        result = encryptor.encrypt_fields(vars_)
        assert result.encrypted["DB_PASS"].startswith(ENCRYPTED_PREFIX)
        assert result.encrypted["APP_NAME"].startswith(ENCRYPTED_PREFIX)
        assert not result.errors

    def test_encrypt_selected_keys_only(self, encryptor):
        vars_ = {"DB_PASS": "secret", "APP_NAME": "myapp"}
        result = encryptor.encrypt_fields(vars_, keys=["DB_PASS"])
        assert result.encrypted["DB_PASS"].startswith(ENCRYPTED_PREFIX)
        assert result.encrypted["APP_NAME"] == "myapp"  # unchanged

    def test_already_encrypted_is_skipped(self, encryptor):
        vars_ = {"DB_PASS": f"{ENCRYPTED_PREFIX}someblob"}
        result = encryptor.encrypt_fields(vars_)
        assert "DB_PASS" in result.skipped
        assert result.encrypted["DB_PASS"] == f"{ENCRYPTED_PREFIX}someblob"

    def test_decrypt_roundtrip(self, encryptor):
        vars_ = {"SECRET": "my-value", "PLAIN": "hello"}
        enc_result = encryptor.encrypt_fields(vars_)
        dec_result = encryptor.decrypt_fields(enc_result.encrypted)
        assert dec_result.encrypted["SECRET"] == "my-value"
        assert dec_result.encrypted["PLAIN"] == "hello"

    def test_decrypt_skips_plain_values(self, encryptor):
        vars_ = {"PLAIN": "not-encrypted"}
        result = encryptor.decrypt_fields(vars_)
        assert "PLAIN" in result.skipped
        assert result.encrypted["PLAIN"] == "not-encrypted"

    def test_decrypt_selected_keys_only(self, encryptor):
        vars_ = {"A": "val-a", "B": "val-b"}
        enc = encryptor.encrypt_fields(vars_)
        dec = encryptor.decrypt_fields(enc.encrypted, keys=["A"])
        assert dec.encrypted["A"] == "val-a"
        assert dec.encrypted["B"].startswith(ENCRYPTED_PREFIX)

    def test_wrong_password_produces_error(self):
        enc = EnvFieldEncryptor("correct-password")
        wrong = EnvFieldEncryptor("wrong-password")
        vars_ = {"SECRET": "value"}
        enc_result = enc.encrypt_fields(vars_)
        dec_result = wrong.decrypt_fields(enc_result.encrypted)
        assert "SECRET" in dec_result.errors

    def test_is_encrypted_static_method(self):
        assert EnvFieldEncryptor.is_encrypted(f"{ENCRYPTED_PREFIX}blob") is True
        assert EnvFieldEncryptor.is_encrypted("plaintext") is False

    def test_empty_vars_returns_empty_result(self, encryptor):
        result = encryptor.encrypt_fields({})
        assert result.encrypted == {}
        assert result.skipped == []
        assert result.errors == {}
