"""Tests for envoy.cli_required."""
import io
import os
import pytest
from envoy.cli_required import handle_required_command


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=secret\n")
    return str(p)


@pytest.fixture
def env_file_empty_val(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=\nAPI_KEY=secret\n")
    return str(p)


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _args(**kwargs):
    defaults = {"required_cmd": "check", "allow_empty": False}
    defaults.update(kwargs)
    return Args(**defaults)


def _out():
    return io.StringIO()


class TestHandleRequiredCommand:
    def test_no_subcommand_shows_usage(self):
        out = _out()
        rc = handle_required_command(Args(required_cmd=None), out=out)
        assert rc == 1
        assert "Usage" in out.getvalue()

    def test_unknown_subcommand_returns_error(self):
        out = _out()
        rc = handle_required_command(Args(required_cmd="bogus"), out=out)
        assert rc == 1

    def test_missing_file_returns_error(self, tmp_path):
        out = _out()
        rc = handle_required_command(
            _args(file=str(tmp_path / "missing.env"), keys=["FOO"]), out=out
        )
        assert rc == 1
        assert "not found" in out.getvalue()

    def test_all_keys_satisfied_returns_zero(self, env_file):
        out = _out()
        rc = handle_required_command(
            _args(file=env_file, keys=["DB_HOST", "DB_PORT", "API_KEY"]), out=out
        )
        assert rc == 0
        assert "satisfied" in out.getvalue()

    def test_missing_key_returns_nonzero(self, env_file):
        out = _out()
        rc = handle_required_command(
            _args(file=env_file, keys=["DB_HOST", "MISSING_KEY"]), out=out
        )
        assert rc == 1
        assert "MISSING" in out.getvalue()
        assert "MISSING_KEY" in out.getvalue()

    def test_empty_value_returns_nonzero(self, env_file_empty_val):
        out = _out()
        rc = handle_required_command(
            _args(file=env_file_empty_val, keys=["DB_HOST", "DB_PORT"]), out=out
        )
        assert rc == 1
        assert "EMPTY" in out.getvalue()
        assert "DB_PORT" in out.getvalue()

    def test_allow_empty_flag_passes_empty_values(self, env_file_empty_val):
        out = _out()
        rc = handle_required_command(
            _args(
                file=env_file_empty_val,
                keys=["DB_HOST", "DB_PORT"],
                allow_empty=True,
            ),
            out=out,
        )
        assert rc == 0
