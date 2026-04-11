"""Tests for envoy.cli_pin."""
import json
from io import StringIO
from pathlib import Path

import pytest

from envoy.cli_pin import handle_pin_command


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("NODE_ENV=development\nLOG_LEVEL=debug\nPORT=3000\n")
    return p


def _args(**kwargs):
    return Args(**kwargs)


def _out():
    return StringIO()


class TestHandlePinCommand:
    def test_no_subcommand_shows_usage(self):
        buf = _out()
        rc = handle_pin_command(_args(pin_cmd=None), out=buf)
        assert rc == 1
        assert "Usage" in buf.getvalue()

    def test_invalid_pins_json_returns_error(self, env_file):
        buf = _out()
        rc = handle_pin_command(
            _args(pin_cmd="check", file=str(env_file), pins="{bad json}"),
            out=buf
        )
        assert rc == 1
        assert "invalid --pins JSON" in buf.getvalue()

    def test_missing_file_returns_error(self, tmp_path):
        buf = _out()
        rc = handle_pin_command(
            _args(pin_cmd="check", file=str(tmp_path / "missing.env"),
                  pins=json.dumps({"NODE_ENV": "production"})),
            out=buf
        )
        assert rc == 1
        assert "file not found" in buf.getvalue()

    def test_check_passes_when_pins_satisfied(self, env_file):
        buf = _out()
        rc = handle_pin_command(
            _args(pin_cmd="check", file=str(env_file),
                  pins=json.dumps({"NODE_ENV": "development"})),
            out=buf
        )
        assert rc == 0
        assert "satisfied" in buf.getvalue()

    def test_check_fails_with_violation(self, env_file):
        buf = _out()
        rc = handle_pin_command(
            _args(pin_cmd="check", file=str(env_file),
                  pins=json.dumps({"NODE_ENV": "production"})),
            out=buf
        )
        assert rc == 1
        assert "VIOLATION" in buf.getvalue()
        assert "NODE_ENV" in buf.getvalue()

    def test_apply_writes_pinned_values(self, env_file):
        buf = _out()
        rc = handle_pin_command(
            _args(pin_cmd="apply", file=str(env_file), output=None,
                  pins=json.dumps({"NODE_ENV": "production"})),
            out=buf
        )
        assert rc == 0
        assert "applied" in buf.getvalue()
        assert "NODE_ENV=production" in env_file.read_text()

    def test_apply_writes_to_output_file(self, env_file, tmp_path):
        out_file = tmp_path / "out.env"
        buf = _out()
        rc = handle_pin_command(
            _args(pin_cmd="apply", file=str(env_file),
                  output=str(out_file),
                  pins=json.dumps({"NODE_ENV": "production"})),
            out=buf
        )
        assert rc == 0
        assert out_file.exists()
        assert "NODE_ENV=production" in out_file.read_text()
