"""Tests for CLI chain command handler."""
import argparse
from pathlib import Path
import pytest

from envoy.cli_chain import handle_chain_command


@pytest.fixture
def env_file_a(tmp_path: Path) -> Path:
    f = tmp_path / "base.env"
    f.write_text("HOST=localhost\nPORT=5432\nDEBUG=false\n")
    return f


@pytest.fixture
def env_file_b(tmp_path: Path) -> Path:
    f = tmp_path / "prod.env"
    f.write_text("HOST=prod.example.com\nSECRET=abc123\n")
    return f


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _args(**kwargs):
    defaults = {"chain_cmd": "merge", "files": [], "show_overrides": False}
    defaults.update(kwargs)
    return Args(**defaults)


def _out():
    lines = []
    def capture(msg=""):
        lines.append(msg)
    capture.lines = lines
    return capture


class TestHandleChainCommand:
    def test_no_subcommand_shows_usage(self):
        out = _out()
        rc = handle_chain_command(Args(chain_cmd=None), out)
        assert rc == 1
        assert any("Usage" in l for l in out.lines)

    def test_missing_file_returns_error(self, tmp_path):
        out = _out()
        args = _args(files=[str(tmp_path / "missing.env")])
        rc = handle_chain_command(args, out)
        assert rc == 1
        assert any("not found" in l for l in out.lines)

    def test_merge_two_files(self, env_file_a, env_file_b):
        out = _out()
        args = _args(files=[str(env_file_a), str(env_file_b)])
        rc = handle_chain_command(args, out)
        assert rc == 0
        combined = "\n".join(out.lines)
        assert "HOST=prod.example.com" in combined
        assert "PORT=5432" in combined
        assert "SECRET=abc123" in combined

    def test_show_overrides_flag(self, env_file_a, env_file_b):
        out = _out()
        args = _args(files=[str(env_file_a), str(env_file_b)], show_overrides=True)
        rc = handle_chain_command(args, out)
        assert rc == 0
        combined = "\n".join(out.lines)
        assert "HOST" in combined
        assert "overridden" in combined.lower()

    def test_unknown_subcommand(self):
        out = _out()
        rc = handle_chain_command(Args(chain_cmd="bogus"), out)
        assert rc == 1
