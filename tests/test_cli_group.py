"""Tests for cli_group handle_group_command."""
import os
import pytest
from envoy.cli_group import handle_group_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=mydb\n"
        "AWS_KEY=abc\n"
        "AWS_SECRET=xyz\n"
        "DEBUG=false\n"
    )
    return str(p)


def _out():
    lines = []
    def capture(msg=""):
        lines.append(str(msg))
    capture.lines = lines
    return capture


class TestHandleGroupCommand:
    def test_no_subcommand_shows_usage(self):
        out = _out()
        args = Args(group_cmd=None)
        rc = handle_group_command(args, out=out)
        assert rc == 1
        assert any("Usage" in l for l in out.lines)

    def test_unknown_subcommand(self):
        out = _out()
        args = Args(group_cmd="nonexistent")
        rc = handle_group_command(args, out=out)
        assert rc == 1

    def test_show_missing_file(self, tmp_path):
        out = _out()
        args = Args(group_cmd="show", file=str(tmp_path / "missing.env"),
                    prefixes=None, min_size=2)
        rc = handle_group_command(args, out=out)
        assert rc == 1
        assert any("not found" in l for l in out.lines)

    def test_show_auto_groups(self, env_file):
        out = _out()
        args = Args(group_cmd="show", file=env_file, prefixes=None, min_size=2)
        rc = handle_group_command(args, out=out)
        assert rc == 0
        combined = "\n".join(out.lines)
        assert "[DB]" in combined
        assert "[AWS]" in combined
        assert "DB_HOST=localhost" in combined

    def test_show_explicit_prefixes(self, env_file):
        out = _out()
        args = Args(group_cmd="show", file=env_file, prefixes=["DB"], min_size=2)
        rc = handle_group_command(args, out=out)
        assert rc == 0
        combined = "\n".join(out.lines)
        assert "[DB]" in combined
        assert "[ungrouped]" in combined

    def test_show_summary_line(self, env_file):
        out = _out()
        args = Args(group_cmd="show", file=env_file, prefixes=None, min_size=2)
        handle_group_command(args, out=out)
        summary = out.lines[-1]
        assert "group" in summary
        assert "ungrouped" in summary
