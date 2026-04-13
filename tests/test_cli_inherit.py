"""Tests for CLI inherit subcommand handler."""
import argparse
from pathlib import Path
import pytest

from envoy.cli_inherit import handle_inherit_command


@pytest.fixture
def base_env_file(tmp_path: Path) -> Path:
    f = tmp_path / "base.env"
    f.write_text("APP_ENV=production\nDB_HOST=db.prod\nLOG_LEVEL=warn\n")
    return f


@pytest.fixture
def child_env_file(tmp_path: Path) -> Path:
    f = tmp_path / "child.env"
    f.write_text("APP_ENV=staging\nEXTRA_KEY=hello\n")
    return f


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "inherit_cmd": "run",
        "no_empty_override": False,
        "show_source": False,
    }
    defaults.update(kwargs)
    ns = argparse.Namespace()
    ns.__dict__.update(defaults)
    return ns


def _out():
    lines = []
    return lines, lines.append


class TestHandleInheritCommand:
    def test_no_subcommand_shows_usage(self):
        lines, capture = _out()
        rc = handle_inherit_command(argparse.Namespace(), capture)
        assert rc == 1
        assert any("Usage" in l for l in lines)

    def test_missing_base_file_returns_error(self, tmp_path, child_env_file):
        lines, capture = _out()
        args = _args(base=str(tmp_path / "missing.env"), child=str(child_env_file))
        rc = handle_inherit_command(args, capture)
        assert rc == 1
        assert any("base file not found" in l for l in lines)

    def test_missing_child_file_returns_error(self, tmp_path, base_env_file):
        lines, capture = _out()
        args = _args(base=str(base_env_file), child=str(tmp_path / "missing.env"))
        rc = handle_inherit_command(args, capture)
        assert rc == 1
        assert any("child file not found" in l for l in lines)

    def test_run_outputs_merged_vars(self, base_env_file, child_env_file):
        lines, capture = _out()
        args = _args(base=str(base_env_file), child=str(child_env_file))
        rc = handle_inherit_command(args, capture)
        assert rc == 0
        joined = "\n".join(lines)
        assert "APP_ENV=staging" in joined
        assert "DB_HOST=db.prod" in joined
        assert "EXTRA_KEY=hello" in joined

    def test_show_source_flag_annotates_output(self, base_env_file, child_env_file):
        lines, capture = _out()
        args = _args(base=str(base_env_file), child=str(child_env_file), show_source=True)
        rc = handle_inherit_command(args, capture)
        assert rc == 0
        joined = "\n".join(lines)
        assert "[child]" in joined or "[base]" in joined

    def test_unknown_subcommand_returns_error(self):
        lines, capture = _out()
        args = argparse.Namespace(inherit_cmd="bogus")
        rc = handle_inherit_command(args, capture)
        assert rc == 1
