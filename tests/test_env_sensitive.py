"""Tests for EnvSensitiveClassifier."""
import pytest
from envoy.env_sensitive import EnvSensitiveClassifier, SensitiveResult, SensitiveEntry


@pytest.fixture
def classifier():
    return EnvSensitiveClassifier()


@pytest.fixture
def sample_vars():
    return {
        "DATABASE_PASSWORD": "s3cr3t",
        "API_TOKEN": "tok_abc123",
        "APP_NAME": "myapp",
        "PORT": "8080",
        "PRIVATE_KEY": "-----BEGIN RSA",
        "DB_URL": "postgres://localhost/db",
    }


class TestSensitiveResult:
    def test_repr(self):
        r = SensitiveResult(scanned=5)
        assert "scanned=5" in repr(r)

    def test_found_false_when_empty(self):
        r = SensitiveResult(scanned=3)
        assert r.found is False

    def test_found_true_when_entries_present(self):
        entry = SensitiveEntry(key="SECRET", value="x", category="credential", confidence="high")
        r = SensitiveResult(entries=[entry], scanned=1)
        assert r.found is True

    def test_high_confidence_filter(self):
        e1 = SensitiveEntry(key="A", value="", category="credential", confidence="high")
        e2 = SensitiveEntry(key="B", value="", category="generic", confidence="low")
        r = SensitiveResult(entries=[e1, e2], scanned=2)
        assert r.high_confidence == [e1]


class TestEnvSensitiveClassifier:
    def test_password_key_detected(self, classifier):
        result = classifier.classify({"DATABASE_PASSWORD": "secret"})
        assert result.found
        assert result.entries[0].category == "credential"

    def test_token_key_detected(self, classifier):
        result = classifier.classify({"API_TOKEN": "tok_123"})
        assert result.found
        assert result.entries[0].category == "token"

    def test_safe_key_not_detected(self, classifier):
        result = classifier.classify({"APP_NAME": "myapp", "PORT": "8080"})
        assert not result.found

    def test_private_key_is_high_confidence(self, classifier):
        result = classifier.classify({"PRIVATE_KEY": "-----BEGIN"})
        assert result.entries[0].confidence == "high"

    def test_scanned_count_matches_input(self, classifier, sample_vars):
        result = classifier.classify(sample_vars)
        assert result.scanned == len(sample_vars)

    def test_multiple_sensitive_keys_detected(self, classifier, sample_vars):
        result = classifier.classify(sample_vars)
        keys = [e.key for e in result.entries]
        assert "DATABASE_PASSWORD" in keys
        assert "API_TOKEN" in keys
        assert "APP_NAME" not in keys

    def test_extra_patterns_extend_detection(self):
        c = EnvSensitiveClassifier(extra_patterns={"internal": ["internal_secret"]})
        result = c.classify({"MY_INTERNAL_SECRET_KEY": "val"})
        assert result.found

    def test_entry_repr(self):
        e = SensitiveEntry(key="TOKEN", value="x", category="token", confidence="high")
        assert "TOKEN" in repr(e)
        assert "token" in repr(e)
