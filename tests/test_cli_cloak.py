"""Tests for handle_cloak_command."""
import os
import pytest
from envoy.cli_cloak import handle_cloak_command


class Args:
    def __init__(self, file=None, patterns=None, symbol="<cloaked>"):
        self.file = file
        self.patterns = patterns or []
        self.symbol = symbol


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nDB_PASSWORD=s3cr3t\nAPI_TOKEN=abc123\nDEBUG=true\n")
    return str(p)


@pytest.fixture
def _out():
    lines = []
    return lines, lines.append


def test_no_file_attr_shows_usage(_out):
    lines, out = _out
    rc = handle_cloak_command(object(), print_fn=out)
    assert rc == 1
    assert any("Usage" in l for l in lines)


def test_missing_file_returns_error(tmp_path, _out):
    lines, out = _out
    rc = handle_cloak_command(Args(file=str(tmp_path / "missing.env")), print_fn=out)
    assert rc == 1
    assert any("not found" in l for l in lines)


def test_no_patterns_returns_error(env_file, _out):
    lines, out = _out
    rc = handle_cloak_command(Args(file=env_file, patterns=[]), print_fn=out)
    assert rc == 1
    assert any("pattern" in l for l in lines)


def test_cloak_matching_vars(env_file, _out):
    lines, out = _out
    rc = handle_cloak_command(
        Args(file=env_file, patterns=["password", "token"]), print_fn=out
    )
    assert rc == 0
    combined = "\n".join(lines)
    assert "DB_PASSWORD" in combined
    assert "API_TOKEN" in combined


def test_no_match_reports_none(env_file, _out):
    lines, out = _out
    rc = handle_cloak_command(
        Args(file=env_file, patterns=["zzznomatch"]), print_fn=out
    )
    assert rc == 0
    assert any("No variables" in l for l in lines)


def test_custom_symbol_in_output(env_file, _out):
    lines, out = _out
    rc = handle_cloak_command(
        Args(file=env_file, patterns=["password"], symbol="[HIDDEN]"), print_fn=out
    )
    assert rc == 0
    combined = "\n".join(lines)
    assert "[HIDDEN]" in combined
