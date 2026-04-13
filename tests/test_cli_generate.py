"""Tests for CLI generate subcommand handler."""
import json
import io
import pytest
from envoy.cli_generate import handle_generate_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def spec_file(tmp_path):
    spec = {
        "fields": [
            {"key": "APP_ENV", "default": "production"},
            {"key": "SECRET_KEY", "auto": "secret"},
            {"key": "APP_ID", "auto": "uuid"},
        ]
    }
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    return str(p)


@pytest.fixture
def _out():
    return io.StringIO()


def test_no_subcommand_shows_usage(spec_file, _out):
    args = Args(generate_cmd=None)
    rc = handle_generate_command(args, out=_out)
    assert rc == 1
    assert "Usage" in _out.getvalue()


def test_run_outputs_env_content(spec_file, _out):
    args = Args(generate_cmd="run", spec=spec_file, out=None, length=32)
    rc = handle_generate_command(args, out=_out)
    assert rc == 0
    output = _out.getvalue()
    assert "APP_ENV=production" in output
    assert "SECRET_KEY=" in output
    assert "APP_ID=" in output


def test_run_writes_to_file(spec_file, tmp_path, _out):
    out_path = str(tmp_path / "output.env")
    args = Args(generate_cmd="run", spec=spec_file, out=out_path, length=32)
    rc = handle_generate_command(args, out=_out)
    assert rc == 0
    assert "Generated" in _out.getvalue()
    content = open(out_path).read()
    assert "APP_ENV=production" in content


def test_missing_spec_file_returns_error(_out):
    args = Args(generate_cmd="run", spec="/nonexistent/spec.json", out=None, length=32)
    rc = handle_generate_command(args, out=_out)
    assert rc == 1
    assert "Error" in _out.getvalue()


def test_invalid_json_spec_returns_error(tmp_path, _out):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    args = Args(generate_cmd="run", spec=str(bad), out=None, length=32)
    rc = handle_generate_command(args, out=_out)
    assert rc == 1
    assert "invalid JSON" in _out.getvalue()


def test_required_field_missing_returns_error(tmp_path, _out):
    spec = {"fields": [{"key": "DB_PASS", "required": True}]}
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    args = Args(generate_cmd="run", spec=str(p), out=None, length=32)
    rc = handle_generate_command(args, out=_out)
    assert rc == 1
    assert "Error" in _out.getvalue()


def test_unknown_subcommand_returns_error(_out):
    args = Args(generate_cmd="unknown")
    rc = handle_generate_command(args, out=_out)
    assert rc == 1
