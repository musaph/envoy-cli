"""Tests for CLI index subcommands."""
import io
import pytest
from envoy.cli_index import handle_index_command


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=envoy\nSECRET=\n")
    return str(f)


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _args(**kwargs):
    defaults = {"index_cmd": None, "file": None, "prefix": None, "as_json": False}
    defaults.update(kwargs)
    return Args(**defaults)


def _out():
    return io.StringIO()


class TestHandleIndexCommand:
    def test_no_subcommand_shows_usage(self):
        out = _out()
        rc = handle_index_command(_args(), out=out)
        assert rc == 1
        assert "Usage" in out.getvalue()

    def test_missing_file_returns_error(self):
        out = _out()
        rc = handle_index_command(_args(index_cmd="build", file="/no/such/file.env"), out=out)
        assert rc == 2
        assert "not found" in out.getvalue()

    def test_build_lists_keys(self, env_file):
        out = _out()
        rc = handle_index_command(_args(index_cmd="build", file=env_file), out=out)
        assert rc == 0
        text = out.getvalue()
        assert "DB_HOST" in text
        assert "APP_NAME" in text

    def test_build_with_prefix_filter(self, env_file):
        out = _out()
        rc = handle_index_command(_args(index_cmd="build", file=env_file, prefix="DB"), out=out)
        assert rc == 0
        text = out.getvalue()
        assert "DB_HOST" in text
        assert "APP_NAME" not in text

    def test_build_json_output(self, env_file):
        import json
        out = _out()
        rc = handle_index_command(_args(index_cmd="build", file=env_file, as_json=True), out=out)
        assert rc == 0
        data = json.loads(out.getvalue())
        assert isinstance(data, list)
        assert any(e["key"] == "DB_HOST" for e in data)

    def test_empty_subcommand_lists_empty_keys(self, env_file):
        out = _out()
        rc = handle_index_command(_args(index_cmd="empty", file=env_file), out=out)
        assert rc == 0
        assert "SECRET" in out.getvalue()

    def test_empty_subcommand_no_empty_keys(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("FOO=bar\nBAZ=qux\n")
        out = _out()
        rc = handle_index_command(_args(index_cmd="empty", file=str(f)), out=out)
        assert rc == 0
        assert "No empty" in out.getvalue()

    def test_unknown_subcommand_returns_error(self, env_file):
        out = _out()
        rc = handle_index_command(_args(index_cmd="bogus", file=env_file), out=out)
        assert rc == 1
