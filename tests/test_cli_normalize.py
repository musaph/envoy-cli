"""Tests for handle_normalize_command."""
import os
import pytest
from envoy.cli_normalize import handle_normalize_command


class Args:
    def __init__(self, file, no_strip_quotes=False, no_fix_line_endings=False, dry_run=False):
        self.file = file
        self.no_strip_quotes = no_strip_quotes
        self.no_fix_line_endings = no_fix_line_endings
        self.dry_run = dry_run


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text('KEY="hello"\nSPACED=  world  \nCLEAN=ok\n', encoding="utf-8")
    return str(f)


@pytest.fixture
def clean_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=hello\nCLEAN=ok\n", encoding="utf-8")
    return str(f)


@pytest.fixture
def _out():
    lines = []
    return lines, lines.append


def test_no_file_attr_shows_usage(_out):
    lines, out = _out

    class NoFile:
        pass

    rc = handle_normalize_command(NoFile(), out=out)
    assert rc == 1
    assert any("Usage" in l for l in lines)


def test_missing_file_returns_error(tmp_path, _out):
    lines, out = _out
    rc = handle_normalize_command(Args(file=str(tmp_path / "missing.env")), out=out)
    assert rc == 1
    assert any("not found" in l for l in lines)


def test_clean_file_reports_no_changes(clean_env_file, _out):
    lines, out = _out
    rc = handle_normalize_command(Args(file=clean_env_file), out=out)
    assert rc == 0
    assert any("No normalization" in l for l in lines)


def test_normalize_writes_file(env_file, _out):
    lines, out = _out
    rc = handle_normalize_command(Args(file=env_file), out=out)
    assert rc == 0
    content = open(env_file).read()
    assert '"hello"' not in content
    assert "hello" in content


def test_dry_run_does_not_write(env_file, _out):
    lines, out = _out
    original = open(env_file).read()
    rc = handle_normalize_command(Args(file=env_file, dry_run=True), out=out)
    assert rc == 0
    assert open(env_file).read() == original
    assert any("Dry run" in l for l in lines)


def test_no_strip_quotes_leaves_quoted_values(env_file, _out):
    lines, out = _out
    rc = handle_normalize_command(Args(file=env_file, no_strip_quotes=True), out=out)
    assert rc == 0
    content = open(env_file).read()
    assert '"hello"' in content
