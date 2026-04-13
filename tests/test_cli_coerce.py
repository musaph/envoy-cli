"""Tests for CLI coerce subcommand handler."""
import io
import os
import pytest
from envoy.cli_coerce import handle_coerce_command


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY=  hello  \nFLAG=yes\n")
    return str(p)


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _args(**kwargs):
    defaults = dict(coerce_cmd=None, file=None, rules=["strip"], dry_run=False)
    defaults.update(kwargs)
    return Args(**defaults)


def _out():
    return io.StringIO()


class TestHandleCoerceCommand:
    def test_no_subcommand_shows_usage(self):
        out = _out()
        rc = handle_coerce_command(_args(coerce_cmd=None), out=out)
        assert rc == 1
        assert "Usage" in out.getvalue()

    def test_rules_lists_available_rules(self):
        out = _out()
        rc = handle_coerce_command(_args(coerce_cmd="rules"), out=out)
        assert rc == 0
        text = out.getvalue()
        assert "strip" in text
        assert "uppercase" in text
        assert "bool_normalize" in text

    def test_run_missing_file_returns_error(self):
        out = _out()
        rc = handle_coerce_command(
            _args(coerce_cmd="run", file="/nonexistent/.env"), out=out
        )
        assert rc == 1
        assert "not found" in out.getvalue()

    def test_run_unknown_rule_returns_error(self, env_file):
        out = _out()
        rc = handle_coerce_command(
            _args(coerce_cmd="run", file=env_file, rules=["bogus"]), out=out
        )
        assert rc == 1
        assert "Error" in out.getvalue()

    def test_run_dry_run_no_write(self, env_file):
        original = open(env_file).read()
        out = _out()
        rc = handle_coerce_command(
            _args(coerce_cmd="run", file=env_file, rules=["strip"], dry_run=True),
            out=out,
        )
        assert rc == 0
        assert open(env_file).read() == original
        assert "Dry run" in out.getvalue()

    def test_run_writes_changes(self, env_file):
        out = _out()
        rc = handle_coerce_command(
            _args(coerce_cmd="run", file=env_file, rules=["strip"], dry_run=False),
            out=out,
        )
        assert rc == 0
        content = open(env_file).read()
        assert "  hello  " not in content
        assert "Written" in out.getvalue()

    def test_run_no_changes_reports_clean(self, tmp_path):
        p = tmp_path / ".env"
        p.write_text("KEY=hello\n")
        out = _out()
        rc = handle_coerce_command(
            _args(coerce_cmd="run", file=str(p), rules=["strip"]), out=out
        )
        assert rc == 0
        assert "No changes" in out.getvalue()

    def test_unknown_subcommand_returns_error(self):
        out = _out()
        rc = handle_coerce_command(_args(coerce_cmd="unknown"), out=out)
        assert rc == 1
