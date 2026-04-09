"""Tests for handle_import_command in envoy/cli_import.py."""
import io
import json
from pathlib import Path

import pytest

from envoy.cli_import import handle_import_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / "sample.env"
    p.write_text("HELLO=world\nFOO=bar\n")
    return p


@pytest.fixture()
def json_file(tmp_path):
    p = tmp_path / "sample.json"
    p.write_text(json.dumps({"DB_HOST": "localhost", "DB_PORT": "5432"}))
    return p


def _args(**kwargs):
    defaults = dict(file=None, format=None, output=None, merge=None)
    defaults.update(kwargs)
    return Args(**defaults)


class TestHandleImportCommand:
    def test_no_file_attr_shows_usage(self):
        out, err = io.StringIO(), io.StringIO()
        rc = handle_import_command(Args(), out=out, err=err)
        assert rc == 1
        assert "Usage" in err.getvalue()

    def test_missing_file_reports_error(self, tmp_path):
        out, err = io.StringIO(), io.StringIO()
        rc = handle_import_command(_args(file=str(tmp_path / "nope.env")),
                                   out=out, err=err)
        assert rc == 1
        assert "not found" in err.getvalue()

    def test_dotenv_to_stdout(self, env_file):
        out, err = io.StringIO(), io.StringIO()
        rc = handle_import_command(_args(file=str(env_file)), out=out, err=err)
        assert rc == 0
        assert "HELLO" in out.getvalue()

    def test_json_to_output_file(self, json_file, tmp_path):
        dest = tmp_path / "out.env"
        out, err = io.StringIO(), io.StringIO()
        rc = handle_import_command(
            _args(file=str(json_file), format="json", output=str(dest)),
            out=out, err=err,
        )
        assert rc == 0
        assert dest.exists()
        content = dest.read_text()
        assert "DB_HOST" in content

    def test_merge_existing_keys_win(self, json_file, tmp_path):
        existing = tmp_path / "existing.env"
        existing.write_text("DB_HOST=override\n")
        out, err = io.StringIO(), io.StringIO()
        rc = handle_import_command(
            _args(file=str(json_file), format="json", merge=str(existing)),
            out=out, err=err,
        )
        assert rc == 0
        assert "override" in out.getvalue()

    def test_bad_json_reports_error(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not-json")
        out, err = io.StringIO(), io.StringIO()
        rc = handle_import_command(_args(file=str(bad), format="json"),
                                   out=out, err=err)
        assert rc == 1
        assert "Error" in err.getvalue()
