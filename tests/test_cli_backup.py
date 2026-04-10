"""Tests for CLI backup subcommands."""
from __future__ import annotations

import io
import pytest
from pathlib import Path

from envoy.cli_backup import handle_backup_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    return str(p)


def _out():
    return io.StringIO()


class TestHandleBackupCommand:
    def test_no_subcommand_shows_usage(self, tmp_dir):
        args = Args(backup_cmd=None)
        buf = _out()
        rc = handle_backup_command(args, tmp_dir, output=buf)
        assert rc == 1
        assert "Usage" in buf.getvalue()

    def test_create_success(self, tmp_dir, env_file):
        args = Args(backup_cmd="create", file=env_file, key="prod", note="ci")
        buf = _out()
        rc = handle_backup_command(args, tmp_dir, output=buf)
        assert rc == 0
        assert "Backup created" in buf.getvalue()

    def test_create_missing_file(self, tmp_dir):
        args = Args(backup_cmd="create", file="/no/such/file.env", key="prod", note="")
        buf = _out()
        rc = handle_backup_command(args, tmp_dir, output=buf)
        assert rc == 1
        assert "not found" in buf.getvalue()

    def test_list_empty(self, tmp_dir):
        args = Args(backup_cmd="list", key=None)
        buf = _out()
        rc = handle_backup_command(args, tmp_dir, output=buf)
        assert rc == 0
        assert "No backups" in buf.getvalue()

    def test_list_after_create(self, tmp_dir, env_file):
        create_args = Args(backup_cmd="create", file=env_file, key="prod", note="")
        handle_backup_command(create_args, tmp_dir)
        list_args = Args(backup_cmd="list", key="prod")
        buf = _out()
        rc = handle_backup_command(list_args, tmp_dir, output=buf)
        assert rc == 0
        assert "prod" in buf.getvalue()

    def test_restore_to_file(self, tmp_dir, env_file, tmp_path):
        create_args = Args(backup_cmd="create", file=env_file, key="prod", note="")
        handle_backup_command(create_args, tmp_dir)
        out_path = str(tmp_path / "restored.env")
        restore_args = Args(backup_cmd="restore", key="prod", index=-1, out=out_path)
        buf = _out()
        rc = handle_backup_command(restore_args, tmp_dir, output=buf)
        assert rc == 0
        assert Path(out_path).exists()
        content = Path(out_path).read_text()
        assert "DB_HOST" in content

    def test_restore_missing_key(self, tmp_dir):
        args = Args(backup_cmd="restore", key="ghost", index=-1, out=None)
        buf = _out()
        rc = handle_backup_command(args, tmp_dir, output=buf)
        assert rc == 1
        assert "No backup found" in buf.getvalue()

    def test_delete_backups(self, tmp_dir, env_file):
        for _ in range(3):
            handle_backup_command(Args(backup_cmd="create", file=env_file, key="prod", note=""), tmp_dir)
        buf = _out()
        rc = handle_backup_command(Args(backup_cmd="delete", key="prod"), tmp_dir, output=buf)
        assert rc == 0
        assert "3" in buf.getvalue()
