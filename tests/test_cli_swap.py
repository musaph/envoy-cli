"""Tests for CLI swap subcommands."""
import pytest
from envoy.cli_swap import handle_swap_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("HOST=localhost\nPORT=5432\n")
    return str(f)


def _out(msgs):
    def _inner(msg):
        msgs.append(msg)
    return _inner


def test_no_subcommand_shows_usage():
    msgs = []
    args = Args(swap_cmd=None)
    rc = handle_swap_command(args, out=_out(msgs))
    assert rc == 1
    assert any("Usage" in m for m in msgs)


def test_unknown_subcommand_returns_error():
    msgs = []
    args = Args(swap_cmd="unknown")
    rc = handle_swap_command(args, out=_out(msgs))
    assert rc == 1


def test_missing_file_returns_error(tmp_path):
    msgs = []
    args = Args(swap_cmd="run", file=str(tmp_path / "missing.env"), overwrite=False, dry_run=False)
    rc = handle_swap_command(args, out=_out(msgs))
    assert rc == 2
    assert any("not found" in m for m in msgs)


def test_dry_run_does_not_write(env_file):
    msgs = []
    original = open(env_file).read()
    args = Args(swap_cmd="run", file=env_file, overwrite=False, dry_run=True)
    rc = handle_swap_command(args, out=_out(msgs))
    assert rc == 0
    assert open(env_file).read() == original
    assert any("Dry run" in m for m in msgs)


def test_run_writes_swapped_file(env_file):
    msgs = []
    args = Args(swap_cmd="run", file=env_file, overwrite=False, dry_run=False)
    rc = handle_swap_command(args, out=_out(msgs))
    assert rc == 0
    content = open(env_file).read()
    assert "localhost" in content
    assert "5432" in content


def test_no_swappable_pairs(tmp_path):
    f = tmp_path / ".env"
    f.write_text("EMPTY=\n")
    msgs = []
    args = Args(swap_cmd="run", file=str(f), overwrite=False, dry_run=False)
    rc = handle_swap_command(args, out=_out(msgs))
    assert rc == 0
    assert any("No swappable" in m for m in msgs)
