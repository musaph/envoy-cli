"""Tests for EnvRedactLog."""
import pytest
from envoy.env_redact_log import EnvRedactLog, RedactLogChange, RedactLogResult


@pytest.fixture
def redactor():
    return EnvRedactLog()


@pytest.fixture
def sample_vars():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "PORT": "8080",
        "SECRET_TOKEN": "tok_xyz",
    }


class TestRedactLogResult:
    def test_repr(self):
        result = RedactLogResult()
        assert "RedactLogResult" in repr(result)
        assert "has_changes=False" in repr(result)

    def test_has_changes_false_when_empty(self):
        result = RedactLogResult()
        assert result.has_changes is False

    def test_has_changes_true_when_populated(self):
        change = RedactLogChange(key="X", original_value="v", redacted_value="***REDACTED***")
        result = RedactLogResult(changes=[change], redacted={"X": "***REDACTED***"})
        assert result.has_changes is True

    def test_changed_keys_returns_list(self):
        change = RedactLogChange(key="MY_KEY", original_value="val", redacted_value="***REDACTED***")
        result = RedactLogResult(changes=[change])
        assert result.changed_keys == ["MY_KEY"]


class TestRedactLogChange:
    def test_repr_contains_key(self):
        c = RedactLogChange(key="DB_PASS", original_value="secret", redacted_value="***REDACTED***")
        assert "DB_PASS" in repr(c)


class TestEnvRedactLog:
    def test_non_sensitive_keys_unchanged(self, redactor, sample_vars):
        result = redactor.redact(sample_vars)
        assert result.redacted["APP_NAME"] == "myapp"
        assert result.redacted["PORT"] == "8080"

    def test_sensitive_keys_masked(self, redactor, sample_vars):
        result = redactor.redact(sample_vars)
        assert result.redacted["DB_PASSWORD"] == EnvRedactLog.MASK
        assert result.redacted["API_KEY"] == EnvRedactLog.MASK
        assert result.redacted["SECRET_TOKEN"] == EnvRedactLog.MASK

    def test_changes_only_includes_sensitive(self, redactor, sample_vars):
        result = redactor.redact(sample_vars)
        changed = result.changed_keys
        assert "DB_PASSWORD" in changed
        assert "API_KEY" in changed
        assert "APP_NAME" not in changed
        assert "PORT" not in changed

    def test_empty_vars_returns_empty_result(self, redactor):
        result = redactor.redact({})
        assert result.has_changes is False
        assert result.redacted == {}

    def test_all_safe_vars_no_changes(self, redactor):
        vars = {"HOST": "localhost", "PORT": "5432", "APP": "envoy"}
        result = redactor.redact(vars)
        assert result.has_changes is False
        assert result.redacted == vars

    def test_original_value_preserved_in_change(self, redactor):
        vars = {"DB_PASSWORD": "my_secret"}
        result = redactor.redact(vars)
        assert result.changes[0].original_value == "my_secret"
        assert result.changes[0].redacted_value == EnvRedactLog.MASK
