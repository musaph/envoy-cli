"""Tests for the pivot CLI handler."""
import pytest
from envoy.cli_pivot import handle_pivot_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("HOST=localhost\nPORT=8080\nEMPTY=\n")
    return str(f)


@pytest.fixture
def _out():
    lines = []
    return lines, lines.append


def test_no_subcommand_shows_usage(_out):
    lines, out = _out
    args = Args(pivot_cmd=None)
    rc = handle_pivot_command(args, out)
    assert rc == 1
    assert any("Usage" in l for l in lines)


def test_unknown_subcommand_returns_error(_out):
    lines, out = _out
    args = Args(pivot_cmd="nonexistent")
    rc = handle_pivot_command(args, out)
    assert rc == 1


def test_run_missing_file_returns_error(_out):
    lines, out = _out
    args = Args(pivot_cmd="run", file="/no/such/file.env", on_collision="skip", include_empty=False)
    rc = handle_pivot_command(args, out)
    assert rc == 1
    assert any("not found" in l for l in lines)


def test_run_pivots_vars(env_file, _out):
    lines, out = _out
    args = Args(pivot_cmd="run", file=env_file, on_collision="skip", include_empty=False)
    rc = handle_pivot_command(args, out)
    assert rc == 0
    combined = "\n".join(lines)
    assert "localhost" in combined
    assert "8080" in combined


def test_run_reports_skipped_empty(env_file, _out):
    lines, out = _out
    args = Args(pivot_cmd="run", file=env_file, on_collision="skip", include_empty=False)
    handle_pivot_command(args, out)
    combined = "\n".join(lines)
    assert "EMPTY" in combined or "Skipped" in combined


def test_run_include_empty_flag(env_file, _out):
    lines, out = _out
    args = Args(pivot_cmd="run", file=env_file, on_collision="skip", include_empty=True)
    rc = handle_pivot_command(args, out)
    assert rc == 0
    combined = "\n".join(lines)
    # empty string becomes a key; EMPTY should not appear in skipped
    assert "Skipped" not in combined or "EMPTY" not in combined
