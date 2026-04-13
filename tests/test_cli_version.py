import io
import pytest
from envoy.env_version import EnvVersionManager
from envoy.cli_version import handle_version_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def tmp_env(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP=prod\nDEBUG=false\n")
    return str(f)


@pytest.fixture
def manager():
    return EnvVersionManager()


def _out():
    return io.StringIO()


def test_no_subcommand_shows_usage(manager):
    args = Args(version_cmd=None)
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 1
    assert "Usage" in buf.getvalue()


def test_save_creates_version(tmp_env, manager):
    args = Args(version_cmd="save", file=tmp_env, label=None)
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 0
    assert "Saved version 1" in buf.getvalue()
    assert manager.list().count == 1


def test_save_with_label(tmp_env, manager):
    args = Args(version_cmd="save", file=tmp_env, label="release-1")
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 0
    assert "release-1" in buf.getvalue()


def test_save_missing_file_returns_error(manager):
    args = Args(version_cmd="save", file="/nonexistent/.env", label=None)
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 1
    assert "Error" in buf.getvalue()


def test_list_empty(manager):
    args = Args(version_cmd="list", file="irrelevant")
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 0
    assert "No versions" in buf.getvalue()


def test_list_shows_versions(tmp_env, manager):
    manager.save({"A": "1"}, label="first")
    manager.save({"A": "2"})
    args = Args(version_cmd="list", file=tmp_env)
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 0
    output = buf.getvalue()
    assert "v1" in output
    assert "v2" in output
    assert "first" in output


def test_rollback_restores_file(tmp_path, manager):
    f = tmp_path / ".env"
    f.write_text("APP=prod\n")
    manager.save({"APP": "staging"})
    args = Args(version_cmd="rollback", file=str(f), version=1)
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 0
    assert "Rolled back to version 1" in buf.getvalue()
    assert "APP" in f.read_text()


def test_rollback_missing_version(tmp_env, manager):
    args = Args(version_cmd="rollback", file=tmp_env, version=99)
    buf = _out()
    rc = handle_version_command(args, manager, out=buf)
    assert rc == 1
    assert "Error" in buf.getvalue()
