"""Tests for handle_slugify_command."""
from __future__ import annotations

import pytest

from envoy.cli_slugify import handle_slugify_command


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("myApiKey=secret\nsome-var=123\nALREADY_UPPER=ok\n")
    return str(f)


@pytest.fixture
def _out():
    output = []
    return output, output.append


def test_no_subcommand_shows_usage(_out):
    buf, fn = _out
    args = Args()
    code = handle_slugify_command(args, print_fn=fn)
    assert code == 1
    assert any("Usage" in line for line in buf)


def test_unknown_subcommand_returns_error(_out):
    buf, fn = _out
    args = Args(slugify_cmd="nonexistent")
    code = handle_slugify_command(args, print_fn=fn)
    assert code == 1


def test_missing_file_returns_error(tmp_path, _out):
    buf, fn = _out
    args = Args(
        slugify_cmd="run",
        file=str(tmp_path / "missing.env"),
        overwrite=False,
        dry_run=False,
    )
    code = handle_slugify_command(args, print_fn=fn)
    assert code == 1
    assert any("not found" in line for line in buf)


def test_dry_run_no_changes_written(env_file, _out):
    buf, fn = _out
    args = Args(slugify_cmd="run", file=env_file, overwrite=False, dry_run=True)
    code = handle_slugify_command(args, print_fn=fn)
    assert code == 0
    assert any("Dry-run" in line for line in buf)
    # File should be unchanged
    content = open(env_file).read()
    assert "myApiKey" in content


def test_run_writes_slugified_keys(env_file, _out):
    buf, fn = _out
    args = Args(slugify_cmd="run", file=env_file, overwrite=False, dry_run=False)
    code = handle_slugify_command(args, print_fn=fn)
    assert code == 0
    content = open(env_file).read()
    assert "MY_API_KEY" in content
    assert "SOME_VAR" in content
    assert "ALREADY_UPPER" in content


def test_no_changes_reports_clean(tmp_path, _out):
    buf, fn = _out
    f = tmp_path / ".env"
    f.write_text("CLEAN_KEY=value\nANOTHER_KEY=x\n")
    args = Args(slugify_cmd="run", file=str(f), overwrite=False, dry_run=False)
    code = handle_slugify_command(args, print_fn=fn)
    assert code == 0
    assert any("No keys" in line for line in buf)
