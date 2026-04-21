import pytest
from io import StringIO
from envoy.cli_replace import handle_replace_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nAPP_ENV=localhost_dev\nAPP_NAME=myapp\n")
    return str(p)


def _out():
    return StringIO()


class TestHandleReplaceCommand:
    def test_no_subcommand_shows_usage(self):
        args = Args(replace_cmd=None)
        out = _out()
        rc = handle_replace_command(args, out)
        assert rc == 1
        assert "Usage" in out.getvalue()

    def test_unknown_subcommand_returns_error(self):
        args = Args(replace_cmd="unknown")
        out = _out()
        rc = handle_replace_command(args, out)
        assert rc == 1

    def test_run_missing_file_returns_error(self):
        args = Args(
            replace_cmd="run",
            file="/no/such/file.env",
            pattern="x",
            replacement="y",
            keys=None,
            dry_run=False,
        )
        out = _out()
        rc = handle_replace_command(args, out)
        assert rc == 1
        assert "not found" in out.getvalue()

    def test_run_no_matches_reports_none(self, env_file):
        args = Args(
            replace_cmd="run",
            file=env_file,
            pattern="ZZZNOMATCH",
            replacement="x",
            keys=None,
            dry_run=False,
        )
        out = _out()
        rc = handle_replace_command(args, out)
        assert rc == 0
        assert "No replacements" in out.getvalue()

    def test_run_replaces_and_writes(self, env_file):
        args = Args(
            replace_cmd="run",
            file=env_file,
            pattern="localhost",
            replacement="prod.db",
            keys=None,
            dry_run=False,
        )
        out = _out()
        rc = handle_replace_command(args, out)
        assert rc == 0
        content = open(env_file).read()
        assert "prod.db" in content
        assert "localhost" not in content

    def test_dry_run_does_not_write(self, env_file):
        args = Args(
            replace_cmd="run",
            file=env_file,
            pattern="localhost",
            replacement="staging",
            keys=None,
            dry_run=True,
        )
        out = _out()
        rc = handle_replace_command(args, out)
        assert rc == 0
        content = open(env_file).read()
        assert "localhost" in content
        assert "Dry run" in out.getvalue()
