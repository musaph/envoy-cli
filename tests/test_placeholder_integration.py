"""Integration tests: placeholder detector with parser and redactor."""
import pytest
from envoy.parser import EnvParser
from envoy.env_placeholder import EnvPlaceholderDetector
from envoy.redact import EnvRedactor
from envoy.secrets import SecretScanner


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def detector():
    return EnvPlaceholderDetector()


SAMPLE_ENV = """
DB_HOST=localhost
DB_PASSWORD=<YOUR_DB_PASSWORD>
API_KEY=CHANGE_ME
APP_NAME=myapp
DEBUG=true
SECRET_TOKEN=
"""


class TestPlaceholderWithParser:
    def test_parse_then_detect_finds_all_placeholders(self, parser, detector):
        vars = parser.parse(SAMPLE_ENV)
        result = detector.detect(vars)
        keys = [m.key for m in result.matches]
        assert "DB_PASSWORD" in keys
        assert "API_KEY" in keys
        assert "SECRET_TOKEN" in keys
        assert "DB_HOST" not in keys
        assert "APP_NAME" not in keys

    def test_safe_vars_not_flagged(self, parser, detector):
        safe_env = "HOST=prod.example.com\nPORT=443\nDEBUG=false\n"
        vars = parser.parse(safe_env)
        result = detector.detect(vars)
        assert result.found is False

    def test_placeholder_keys_overlap_with_secrets(self, parser, detector):
        """Placeholder detection and secret scanning can both flag the same key."""
        scanner = SecretScanner()
        vars = parser.parse(SAMPLE_ENV)
        placeholder_result = detector.detect(vars)
        secret_matches = scanner.scan(vars)

        placeholder_keys = {m.key for m in placeholder_result.matches}
        secret_keys = {m.key for m in secret_matches}

        # DB_PASSWORD and API_KEY and SECRET_TOKEN should appear in both
        overlap = placeholder_keys & secret_keys
        assert len(overlap) >= 1

    def test_detect_after_partial_fill(self, parser, detector):
        """After filling in some placeholders, only remaining ones are flagged."""
        vars = parser.parse(SAMPLE_ENV)
        vars["DB_PASSWORD"] = "actualpassword"
        vars["API_KEY"] = "sk-real-key-123"
        result = detector.detect(vars)
        keys = [m.key for m in result.matches]
        assert "DB_PASSWORD" not in keys
        assert "API_KEY" not in keys
        assert "SECRET_TOKEN" in keys  # still empty
