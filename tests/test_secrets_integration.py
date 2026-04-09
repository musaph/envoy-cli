"""Integration tests combining SecretScanner with EnvParser and EnvFile."""

import pytest
from envoy.secrets import SecretScanner, MASK_PLACEHOLDER
from envoy.parser import EnvParser
from envoy.env_file import EnvFile


SAMPLE_ENV = """\
APP_ENV=production
DB_PASSWORD=hunter2
GITHUB_TOKEN=ghp_{'A'*36}
PORT=5432
DEBUG=false
"""


@pytest.fixture
def sample_env_file(tmp_path):
    content = (
        "APP_ENV=production\n"
        "DB_PASSWORD=hunter2\n"
        "PORT=5432\n"
        "DEBUG=false\n"
        "API_KEY=a3f1b2c4d5e6f7a8b9c0d1e2f3a4b5c6\n"
    )
    p = tmp_path / ".env"
    p.write_text(content)
    return EnvFile(str(p))


class TestScannerWithParser:
    def test_parse_then_scan_finds_secrets(self, sample_env_file):
        raw = sample_env_file.read()
        variables = EnvParser.parse(raw)
        scanner = SecretScanner()
        matches = scanner.scan(variables)
        keys_found = {m.key for m in matches}
        assert "DB_PASSWORD" in keys_found
        assert "API_KEY" in keys_found

    def test_parse_then_scan_safe_vars_excluded(self, sample_env_file):
        raw = sample_env_file.read()
        variables = EnvParser.parse(raw)
        scanner = SecretScanner()
        matches = scanner.scan(variables)
        keys_found = {m.key for m in matches}
        assert "PORT" not in keys_found
        assert "DEBUG" not in keys_found

    def test_mask_then_serialize_roundtrip(self, sample_env_file):
        raw = sample_env_file.read()
        variables = EnvParser.parse(raw)
        scanner = SecretScanner()
        masked = scanner.mask(variables)
        serialized = EnvParser.serialize(masked)
        reparsed = EnvParser.parse(serialized)
        assert reparsed["DB_PASSWORD"] == MASK_PLACEHOLDER
        assert reparsed["APP_ENV"] == "production"

    def test_mask_write_and_read_back(self, tmp_path, sample_env_file):
        raw = sample_env_file.read()
        variables = EnvParser.parse(raw)
        scanner = SecretScanner()
        masked = scanner.mask(variables)
        out_path = tmp_path / "masked.env"
        out_file = EnvFile(str(out_path))
        out_file.write(EnvParser.serialize(masked))
        read_back = EnvParser.parse(out_file.read())
        assert read_back["DB_PASSWORD"] == MASK_PLACEHOLDER
        assert read_back["PORT"] == "5432"

    def test_no_false_positives_on_common_vars(self):
        variables = {
            "NODE_ENV": "development",
            "PORT": "3000",
            "LOG_LEVEL": "info",
            "TIMEOUT": "30",
        }
        scanner = SecretScanner()
        matches = scanner.scan(variables)
        assert matches == []
