"""Tests for envoy.cli_secrets module."""

import pytest
from unittest.mock import MagicMock, patch
from envoy.cli_secrets import handle_secrets_command


def _make_args(**kwargs):
    args = MagicMock()
    args.secrets_cmd = kwargs.get("secrets_cmd", None)
    args.file = kwargs.get("file", ".env")
    args.extra_patterns = kwargs.get("extra_patterns", [])
    return args


@pytest.fixture
def env_content():
    return "APP_ENV=production\nDB_PASSWORD=supersecret\nPORT=5432\n"


class TestHandleSecretsCommand:
    def test_no_subcommand_shows_usage(self):
        args = _make_args(secrets_cmd=None)
        out = []
        handle_secrets_command(args, out)
        assert any("Usage" in line for line in out)

    def test_scan_missing_file_reports_error(self, tmp_path):
        args = _make_args(secrets_cmd="scan", file=str(tmp_path / "missing.env"))
        out = []
        handle_secrets_command(args, out)
        assert any("not found" in line for line in out)

    def test_scan_detects_sensitive_key(self, tmp_path, env_content):
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)
        args = _make_args(secrets_cmd="scan", file=str(env_path))
        out = []
        handle_secrets_command(args, out)
        assert any("DB_PASSWORD" in line for line in out)

    def test_scan_no_sensitive_vars(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text("APP_ENV=production\nPORT=5432\n")
        args = _make_args(secrets_cmd="scan", file=str(env_path))
        out = []
        handle_secrets_command(args, out)
        assert any("No sensitive" in line for line in out)

    def test_scan_reports_count(self, tmp_path, env_content):
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)
        args = _make_args(secrets_cmd="scan", file=str(env_path))
        out = []
        handle_secrets_command(args, out)
        assert any("1 sensitive" in line for line in out)

    def test_mask_replaces_sensitive_values(self, tmp_path, env_content):
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)
        args = _make_args(secrets_cmd="mask", file=str(env_path))
        out = []
        handle_secrets_command(args, out)
        combined = "\n".join(out)
        assert "supersecret" not in combined
        assert "MASKED" in combined

    def test_mask_preserves_safe_values(self, tmp_path, env_content):
        env_path = tmp_path / ".env"
        env_path.write_text(env_content)
        args = _make_args(secrets_cmd="mask", file=str(env_path))
        out = []
        handle_secrets_command(args, out)
        combined = "\n".join(out)
        assert "production" in combined

    def test_scan_with_extra_patterns(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text("INTERNAL_REF=abc123\n")
        args = _make_args(
            secrets_cmd="scan",
            file=str(env_path),
            extra_patterns=[r"internal_ref"],
        )
        out = []
        handle_secrets_command(args, out)
        assert any("INTERNAL_REF" in line for line in out)
