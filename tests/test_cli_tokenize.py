"""Tests for handle_tokenize_command."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from envoy.cli_tokenize import handle_tokenize_command


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "ALLOWED_HOSTS=localhost,127.0.0.1\n"
        "TAGS=web api\n"
        "SIMPLE=value\n",
        encoding="utf-8",
    )
    return p


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _args(env_file, **kwargs):
    defaults = dict(
        file=str(env_file),
        pattern=None,
        keys=None,
        min_tokens=2,
        format="text",
    )
    defaults.update(kwargs)
    return Args(**defaults)


def _out():
    return io.StringIO()


class TestHandleTokenizeCommand:
    def test_no_file_attr_shows_usage(self):
        buf = _out()
        rc = handle_tokenize_command(Args(), out=buf)
        assert rc == 1
        assert "Usage" in buf.getvalue()

    def test_missing_file_returns_error(self):
        buf = _out()
        rc = handle_tokenize_command(Args(file="/no/such/.env"), out=buf)
        assert rc == 1
        assert "Error" in buf.getvalue()

    def test_text_output_lists_tokens(self, env_file):
        buf = _out()
        rc = handle_tokenize_command(_args(env_file), out=buf)
        assert rc == 0
        output = buf.getvalue()
        assert "ALLOWED_HOSTS" in output
        assert "localhost" in output

    def test_single_value_shown_as_skipped(self, env_file):
        buf = _out()
        rc = handle_tokenize_command(_args(env_file), out=buf)
        assert rc == 0
        assert "SIMPLE" in buf.getvalue()

    def test_json_output_format(self, env_file):
        buf = _out()
        rc = handle_tokenize_command(_args(env_file, format="json"), out=buf)
        assert rc == 0
        data = json.loads(buf.getvalue())
        assert "ALLOWED_HOSTS" in data
        assert isinstance(data["ALLOWED_HOSTS"], list)

    def test_restrict_keys_via_args(self, env_file):
        buf = _out()
        rc = handle_tokenize_command(_args(env_file, keys=["TAGS"], format="json"), out=buf)
        assert rc == 0
        data = json.loads(buf.getvalue())
        assert list(data.keys()) == ["TAGS"]

    def test_no_changes_message(self, tmp_path):
        p = tmp_path / ".env"
        p.write_text("KEY=singletoken\n", encoding="utf-8")
        buf = _out()
        rc = handle_tokenize_command(_args(p), out=buf)
        assert rc == 0
        assert "No keys" in buf.getvalue()
