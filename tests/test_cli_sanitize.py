import pytest
from pathlib import Path
from io import StringIO
from envoy.cli_sanitize import handle_sanitize_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=  hello  \nPORT=8080\n")
    return f


@pytest.fixture
def clean_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=hello\nPORT=8080\n")
    return f


def _out():
    return StringIO()


def _args(**kwargs):
    defaults = dict(
        sanitize_cmd="run",
        no_strip=False,
        no_control=False,
        max_length=None,
        in_place=False,
    )
    defaults.update(kwargs)
    return Args(**defaults)


class TestHandleSanitizeCommand:
    def test_no_subcommand_shows_usage(self):
        args = Args(sanitize_cmd=None)
        buf = _out()
        rc = handle_sanitize_command(args, out=buf)
        assert rc == 1
        assert "Usage" in buf.getvalue()

    def test_missing_file_returns_error(self, tmp_path):
        args = _args(file=str(tmp_path / "missing.env"))
        buf = _out()
        rc = handle_sanitize_command(args, out=buf)
        assert rc == 1
        assert "not found" in buf.getvalue()

    def test_clean_file_reports_no_changes(self, clean_env_file):
        args = _args(file=str(clean_env_file))
        buf = _out()
        rc = handle_sanitize_command(args, out=buf)
        assert rc == 0
        assert "No sanitization needed" in buf.getvalue()

    def test_dirty_file_reports_changes(self, env_file):
        args = _args(file=str(env_file))
        buf = _out()
        rc = handle_sanitize_command(args, out=buf)
        assert rc == 0
        output = buf.getvalue()
        assert "Sanitized" in output
        assert "KEY" in output

    def test_in_place_writes_file(self, env_file):
        args = _args(file=str(env_file), in_place=True)
        buf = _out()
        rc = handle_sanitize_command(args, out=buf)
        assert rc == 0
        content = env_file.read_text()
        assert "  hello  " not in content

    def test_unknown_subcommand_returns_error(self):
        args = Args(sanitize_cmd="unknown")
        buf = _out()
        rc = handle_sanitize_command(args, out=buf)
        assert rc == 1
        assert "Unknown" in buf.getvalue()
