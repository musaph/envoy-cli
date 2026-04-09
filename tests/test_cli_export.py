"""Tests for envoy.cli_export."""
import io
import os
import pytest

from envoy.cli_export import handle_export_command


ENV_CONTENT = "APP_ENV=staging\nPORT=9000\nSECRET=abc123\n"


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT)
    return str(p)


def _args(**kwargs):
    class Args:
        pass
    a = Args()
    a.file = kwargs.get("file", ".env")
    a.format = kwargs.get("format", "shell")
    a.output = kwargs.get("output", None)
    return a


class TestHandleExportCommand:
    def test_no_file_attr_shows_usage(self):
        class Empty:
            pass
        out = io.StringIO()
        rc = handle_export_command(Empty(), out=out)
        assert rc == 1
        assert "Usage" in out.getvalue()

    def test_missing_file_returns_error(self):
        out = io.StringIO()
        rc = handle_export_command(_args(file="/no/such/file.env"), out=out)
        assert rc == 1
        assert "not found" in out.getvalue()

    def test_shell_export_to_stdout(self, env_file):
        out = io.StringIO()
        rc = handle_export_command(_args(file=env_file, format="shell"), out=out)
        assert rc == 0
        rendered = out.getvalue()
        assert "export APP_ENV=staging" in rendered
        assert "export PORT=9000" in rendered

    def test_docker_format(self, env_file):
        out = io.StringIO()
        rc = handle_export_command(_args(file=env_file, format="docker"), out=out)
        assert rc == 0
        assert "-e APP_ENV=staging" in out.getvalue()

    def test_github_format(self, env_file):
        out = io.StringIO()
        rc = handle_export_command(_args(file=env_file, format="github"), out=out)
        assert rc == 0
        assert ">> $GITHUB_ENV" in out.getvalue()

    def test_output_to_file(self, env_file, tmp_path):
        dest = str(tmp_path / "out.sh")
        out = io.StringIO()
        rc = handle_export_command(_args(file=env_file, format="shell", output=dest), out=out)
        assert rc == 0
        assert os.path.exists(dest)
        content = open(dest).read()
        assert "export APP_ENV=staging" in content
        assert "Exported" in out.getvalue()
