"""Tests for envoy.redact module."""
import pytest
from envoy.redact import EnvRedactor, RedactedVar, DEFAULT_MASK


@pytest.fixture
def redactor() -> EnvRedactor:
    return EnvRedactor()


@pytest.fixture
def partial_redactor() -> EnvRedactor:
    return EnvRedactor(partial=True)


class TestEnvRedactor:
    def test_non_sensitive_key_not_redacted(self, redactor):
        result = redactor.redact_dict({"APP_NAME": "myapp"})
        assert result["APP_NAME"] == "myapp"

    def test_sensitive_key_is_masked(self, redactor):
        result = redactor.redact_dict({"API_KEY": "super-secret"})
        assert result["API_KEY"] == DEFAULT_MASK

    def test_password_key_is_masked(self, redactor):
        result = redactor.redact_dict({"DB_PASSWORD": "hunter2"})
        assert result["DB_PASSWORD"] == DEFAULT_MASK

    def test_token_key_is_masked(self, redactor):
        result = redactor.redact_dict({"AUTH_TOKEN": "abc123"})
        assert result["AUTH_TOKEN"] == DEFAULT_MASK

    def test_mixed_vars_partial_redaction(self, redactor):
        vars = {"APP_ENV": "production", "SECRET_KEY": "topsecret"}
        result = redactor.redact_dict(vars)
        assert result["APP_ENV"] == "production"
        assert result["SECRET_KEY"] == DEFAULT_MASK

    def test_redact_returns_redacted_var_objects(self, redactor):
        results = redactor.redact({"DB_PASS": "12345"})
        assert len(results) == 1
        rv = results[0]
        assert isinstance(rv, RedactedVar)
        assert rv.was_redacted is True
        assert rv.original_value == "12345"
        assert rv.redacted_value == DEFAULT_MASK

    def test_partial_mask_keeps_suffix(self, partial_redactor):
        result = partial_redactor.redact_dict({"API_KEY": "abcdefgh"})
        assert result["API_KEY"].endswith("efgh")
        assert result["API_KEY"].startswith(DEFAULT_MASK)

    def test_partial_mask_short_value_fully_masked(self, partial_redactor):
        result = partial_redactor.redact_dict({"API_KEY": "abc"})
        assert result["API_KEY"] == DEFAULT_MASK

    def test_empty_value_masked(self, redactor):
        result = redactor.redact_dict({"SECRET_KEY": ""})
        assert result["SECRET_KEY"] == DEFAULT_MASK

    def test_custom_mask_string(self):
        r = EnvRedactor(mask="[hidden]")
        result = r.redact_dict({"PASSWORD": "pass"})
        assert result["PASSWORD"] == "[hidden]"

    def test_summary_counts_redacted(self, redactor):
        vars = {"APP_ENV": "prod", "DB_PASSWORD": "secret", "API_KEY": "key"}
        summary = redactor.summary(vars)
        assert summary.startswith("2/3")

    def test_summary_none_redacted(self, redactor):
        vars = {"APP_ENV": "prod", "PORT": "8080"}
        summary = redactor.summary(vars)
        assert summary.startswith("0/2")

    def test_repr_redacted_var(self, redactor):
        results = redactor.redact({"API_KEY": "val"})
        assert "REDACTED" in repr(results[0])

    def test_repr_plain_var(self, redactor):
        results = redactor.redact({"APP_NAME": "val"})
        assert "plain" in repr(results[0])
