"""Tests for envoy.secrets module."""

import pytest
from envoy.secrets import SecretScanner, SecretMatch, MASK_PLACEHOLDER


@pytest.fixture
def scanner():
    return SecretScanner()


class TestSecretScannerKeyDetection:
    def test_detects_password_key(self, scanner):
        assert scanner.is_sensitive_key("DB_PASSWORD") is True

    def test_detects_token_key(self, scanner):
        assert scanner.is_sensitive_key("GITHUB_TOKEN") is True

    def test_detects_api_key(self, scanner):
        assert scanner.is_sensitive_key("STRIPE_API_KEY") is True

    def test_detects_secret_key(self, scanner):
        assert scanner.is_sensitive_key("APP_SECRET") is True

    def test_safe_key_not_flagged(self, scanner):
        assert scanner.is_sensitive_key("APP_ENV") is False

    def test_port_not_flagged(self, scanner):
        assert scanner.is_sensitive_key("PORT") is False


class TestSecretScannerValueDetection:
    def test_detects_hex_string(self, scanner):
        assert scanner.is_sensitive_value("a3f1b2c4d5e6f7a8b9c0d1e2f3a4b5c6") is True

    def test_detects_openai_key(self, scanner):
        assert scanner.is_sensitive_value("sk-abcdefghijklmnopqrstuvwx") is True

    def test_detects_github_token(self, scanner):
        assert scanner.is_sensitive_value("ghp_" + "A" * 36) is True

    def test_short_value_not_flagged(self, scanner):
        assert scanner.is_sensitive_value("true") is False

    def test_plain_url_not_flagged(self, scanner):
        assert scanner.is_sensitive_value("http://localhost:8080") is False


class TestSecretScannerScan:
    def test_scan_returns_matches_for_sensitive_keys(self, scanner):
        variables = {"DB_PASSWORD": "supersecret", "APP_ENV": "production"}
        matches = scanner.scan(variables)
        assert len(matches) == 1
        assert matches[0].key == "DB_PASSWORD"
        assert matches[0].reason == "key name pattern"

    def test_scan_returns_empty_for_safe_vars(self, scanner):
        variables = {"APP_ENV": "production", "PORT": "8080"}
        assert scanner.scan(variables) == []

    def test_scan_detects_sensitive_value(self, scanner):
        variables = {"SOME_VAR": "a3f1b2c4d5e6f7a8b9c0d1e2f3a4b5c6"}
        matches = scanner.scan(variables)
        assert len(matches) == 1
        assert matches[0].reason == "value entropy pattern"

    def test_scan_value_preview_truncated(self, scanner):
        variables = {"API_KEY": "longvaluethatshouldbemaskd"}
        matches = scanner.scan(variables)
        assert matches[0].value_preview.endswith("...")

    def test_scan_empty_variables_returns_empty(self, scanner):
        assert scanner.scan({}) == []


class TestSecretScannerMask:
    def test_mask_replaces_sensitive_values(self, scanner):
        variables = {"DB_PASSWORD": "secret123", "PORT": "5432"}
        masked = scanner.mask(variables)
        assert masked["DB_PASSWORD"] == MASK_PLACEHOLDER
        assert masked["PORT"] == "5432"

    def test_mask_does_not_mutate_original(self, scanner):
        variables = {"DB_PASSWORD": "secret123"}
        masked = scanner.mask(variables)
        assert variables["DB_PASSWORD"] == "secret123"

    def test_mask_returns_new_dict(self, scanner):
        variables = {"DB_PASSWORD": "secret123"}
        masked = scanner.mask(variables)
        assert masked is not variables

    def test_mask_empty_variables_returns_empty(self, scanner):
        assert scanner.mask({}) == {}
