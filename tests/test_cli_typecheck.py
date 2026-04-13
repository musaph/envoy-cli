import json
import os
import pytest
from io import StringIO
from envoy.cli_typecheck import handle_typecheck_command


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("PORT=8080\nDEBUG=true\nAPI_URL=https://api.example.com\n")
    return str(p)


@pytest.fixture
def schema_file(tmp_path):
    schema = {"PORT": "int", "DEBUG": "bool", "API_URL": "url"}
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(schema))
    return str(p)


@pytest.fixture
def bad_schema_file(tmp_path):
    schema = {"PORT": "bool", "DEBUG": "int"}
    p = tmp_path / "bad_schema.json"
    p.write_text(json.dumps(schema))
    return str(p)


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _args(**kwargs):
    defaults = {"typecheck_cmd": "check", "strict": False}
    defaults.update(kwargs)
    return Args(**defaults)


def _out():
    return StringIO()


class TestHandleTypecheckCommand:
    def test_no_subcommand_shows_usage(self):
        out = _out()
        args = Args(typecheck_cmd=None)
        rc = handle_typecheck_command(args, out=out)
        assert rc == 0
        assert "Usage" in out.getvalue()

    def test_unknown_subcommand_returns_error(self):
        out = _out()
        args = Args(typecheck_cmd="unknown")
        rc = handle_typecheck_command(args, out=out)
        assert rc == 1

    def test_missing_env_file_returns_error(self, schema_file):
        out = _out()
        args = _args(file="/no/such/file.env", schema=schema_file)
        rc = handle_typecheck_command(args, out=out)
        assert rc == 1
        assert "not found" in out.getvalue()

    def test_missing_schema_file_returns_error(self, env_file):
        out = _out()
        args = _args(file=env_file, schema="/no/schema.json")
        rc = handle_typecheck_command(args, out=out)
        assert rc == 1
        assert "schema file not found" in out.getvalue()

    def test_valid_env_passes(self, env_file, schema_file):
        out = _out()
        args = _args(file=env_file, schema=schema_file)
        rc = handle_typecheck_command(args, out=out)
        assert rc == 0
        assert "passed" in out.getvalue()

    def test_invalid_env_reports_violations(self, tmp_path, schema_file):
        bad_env = tmp_path / "bad.env"
        bad_env.write_text("PORT=notanint\nDEBUG=maybe\n")
        out = _out()
        args = _args(file=str(bad_env), schema=schema_file)
        rc = handle_typecheck_command(args, out=out)
        assert rc == 0  # non-strict: still returns 0
        assert "violation" in out.getvalue()

    def test_strict_mode_returns_nonzero_on_violations(self, tmp_path, schema_file):
        bad_env = tmp_path / "bad.env"
        bad_env.write_text("PORT=notanint\n")
        out = _out()
        args = _args(file=str(bad_env), schema=schema_file, strict=True)
        rc = handle_typecheck_command(args, out=out)
        assert rc == 1
