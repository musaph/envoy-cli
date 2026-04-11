"""Tests for envoy.env_mask."""
import pytest

from envoy.env_mask import EnvMasker, MaskResult
from envoy.secrets import SecretScanner


@pytest.fixture
def masker() -> EnvMasker:
    return EnvMasker()


@pytest.fixture
def reveal_masker() -> EnvMasker:
    return EnvMasker(reveal_chars=4)


class TestMaskResult:
    def test_repr(self):
        r = MaskResult(original={"A": "1"}, masked={"A": "****"}, masked_keys=["A"])
        assert "MaskResult" in repr(r)

    def test_masked_keys_default_empty(self):
        r = MaskResult(original={}, masked={})
        assert r.masked_keys == []


class TestEnvMasker:
    def test_non_sensitive_key_not_masked(self, masker):
        result = masker.mask({"APP_NAME": "myapp", "PORT": "8080"})
        assert result.masked["APP_NAME"] == "myapp"
        assert result.masked["PORT"] == "8080"
        assert result.masked_keys == []

    def test_sensitive_key_is_masked(self, masker):
        result = masker.mask({"API_KEY": "supersecret"})
        assert result.masked["API_KEY"] == "********"
        assert "API_KEY" in result.masked_keys

    def test_password_key_is_masked(self, masker):
        result = masker.mask({"DB_PASSWORD": "hunter2"})
        assert result.masked["DB_PASSWORD"] == "********"

    def test_token_key_is_masked(self, masker):
        result = masker.mask({"AUTH_TOKEN": "abc123"})
        assert result.masked["AUTH_TOKEN"] == "********"

    def test_empty_value_is_masked(self, masker):
        result = masker.mask({"SECRET": ""})
        assert result.masked["SECRET"] == "********"

    def test_original_preserved(self, masker):
        vars = {"API_KEY": "real_value", "HOST": "localhost"}
        result = masker.mask(vars)
        assert result.original["API_KEY"] == "real_value"

    def test_reveal_chars_appended(self, reveal_masker):
        result = reveal_masker.mask({"API_KEY": "supersecret"})
        assert result.masked["API_KEY"].endswith("cret")
        assert result.masked["API_KEY"].startswith("********")

    def test_reveal_chars_short_value_fully_masked(self, reveal_masker):
        result = reveal_masker.mask({"API_KEY": "ab"})
        assert result.masked["API_KEY"] == "********"

    def test_mask_single_sensitive(self, masker):
        assert masker.mask_single("DB_PASSWORD", "s3cr3t") == "********"

    def test_mask_single_non_sensitive(self, masker):
        assert masker.mask_single("APP_ENV", "production") == "production"

    def test_custom_mask_string(self):
        m = EnvMasker(mask="[REDACTED]")
        result = m.mask({"SECRET_KEY": "abc"})
        assert result.masked["SECRET_KEY"] == "[REDACTED]"

    def test_empty_vars_returns_empty_result(self, masker):
        result = masker.mask({})
        assert result.masked == {}
        assert result.masked_keys == []

    def test_multiple_sensitive_keys_all_masked(self, masker):
        vars = {"API_KEY": "k1", "DB_PASSWORD": "p1", "HOST": "h1"}
        result = masker.mask(vars)
        assert len(result.masked_keys) == 2
        assert result.masked["HOST"] == "h1"
