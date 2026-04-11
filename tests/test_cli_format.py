"""Tests for envoy.cli_format module."""
import pytest
from pathlib import Path
from envoy.cli_format import handle_format_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("db_host=localhost\napi_key=  secret  \n")
    return f


@pytest.fixture
def _args(env_file):
    def make(**kwargs):
        defaults = dict(
            format_cmd="run",
            file=str(env_file),
            no_uppercase=False,
            no_strip=False,
            quote=False,
            remove_empty=False,
            in_place=False,
        )
        defaults.update(kwargs)
        return Args(**defaults)
    return make


class TestHandleFormatCommand:
    def test_no_subcommand_shows_usage(self):
        args = Args(format_cmd=None)
        out = []
        rc = handle_format_command(args, out=out.append)
        assert rc == 1
        assert any("Usage" in line for line in out)

    def test_unknown_subcommand_returns_error(self):
        args = Args(format_cmd="unknown")
        out = []
        rc = handle_format_command(args, out=out.append)
        assert rc == 1

    def test_missing_file_returns_error(self, _args):
        args = _args(file="/nonexistent/.env")
        out = []
        rc = handle_format_command(args, out=out.append)
        assert rc == 1
        assert any("not found" in line for line in out)

    def test_run_outputs_formatted_content(self, _args):
        out = []
        rc = handle_format_command(_args(), out=out.append)
        assert rc == 0
        combined = "\n".join(out)
        assert "DB_HOST" in combined or "API_KEY" in combined

    def test_run_no_changes_message(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("KEY=value\n")
        args = Args(
            format_cmd="run", file=str(f),
            no_uppercase=False, no_strip=False,
            quote=False, remove_empty=False, in_place=False,
        )
        out = []
        rc = handle_format_command(args, out=out.append)
        assert rc == 0
        assert any("No formatting" in line for line in out)

    def test_in_place_writes_file(self, _args, env_file):
        args = _args(in_place=True)
        out = []
        rc = handle_format_command(args, out=out.append)
        assert rc == 0
        content = env_file.read_text()
        assert "DB_HOST" in content
