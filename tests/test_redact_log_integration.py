"""Integration tests for EnvRedactLog with EnvParser and AuditLog."""
import pytest
from envoy.env_redact_log import EnvRedactLog
from envoy.parser import EnvParser
from envoy.audit import AuditLog
import tempfile
import os


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def redactor():
    return EnvRedactLog()


@pytest.fixture
def sample_env_content():
    return (
        "APP_NAME=envoy\n"
        "DB_PASSWORD=supersecret\n"
        "API_KEY=key_abc123\n"
        "PORT=3000\n"
        "DEBUG=true\n"
    )


class TestRedactLogWithParser:
    def test_parse_then_redact_masks_secrets(self, parser, redactor, sample_env_content):
        vars = parser.parse(sample_env_content)
        result = redactor.redact(vars)
        assert result.redacted["DB_PASSWORD"] == EnvRedactLog.MASK
        assert result.redacted["API_KEY"] == EnvRedactLog.MASK
        assert result.redacted["APP_NAME"] == "envoy"
        assert result.redacted["PORT"] == "3000"

    def test_parse_then_redact_change_count(self, parser, redactor, sample_env_content):
        vars = parser.parse(sample_env_content)
        result = redactor.redact(vars)
        # DB_PASSWORD and API_KEY are sensitive
        assert len(result.changes) == 2

    def test_redacted_dict_has_all_keys(self, parser, redactor, sample_env_content):
        vars = parser.parse(sample_env_content)
        result = redactor.redact(vars)
        assert set(result.redacted.keys()) == set(vars.keys())

    def test_audit_log_entry_uses_redacted_values(self, parser, redactor, sample_env_content):
        """Ensure redacted vars can be safely recorded in audit log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            audit = AuditLog(log_path)
            vars = parser.parse(sample_env_content)
            result = redactor.redact(vars)
            # Record a push action with redacted metadata
            audit.record(
                action="push",
                key="test-env",
                metadata={"vars": result.redacted},
            )
            entries = audit.read_all()
            assert len(entries) == 1
            meta_vars = entries[0].metadata["vars"]
            assert meta_vars["DB_PASSWORD"] == EnvRedactLog.MASK
            assert meta_vars["APP_NAME"] == "envoy"
