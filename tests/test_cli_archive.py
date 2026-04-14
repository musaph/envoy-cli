"""Tests for CLI archive subcommands."""
import json
import os
import pytest
from envoy.cli_archive import handle_archive_command


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    return str(p)


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path / "archives.json")


def _out():
    lines = []
    return lines, lines.append


class TestHandleArchiveCommand:
    def test_no_subcommand_shows_usage(self):
        lines, out = _out()
        args = Args(archive_cmd=None)
        rc = handle_archive_command(args, out=out)
        assert rc == 1
        assert any("Usage" in l for l in lines)

    def test_save_creates_archive(self, tmp_env, store_path):
        lines, out = _out()
        args = Args(archive_cmd="save", file=tmp_env, label="v1", store=store_path)
        rc = handle_archive_command(args, out=out)
        assert rc == 0
        assert os.path.exists(store_path)
        assert any("v1" in l for l in lines)

    def test_restore_returns_vars(self, tmp_env, store_path):
        save_args = Args(archive_cmd="save", file=tmp_env, label="v1", store=store_path)
        handle_archive_command(save_args)
        lines, out = _out()
        restore_args = Args(archive_cmd="restore", label="v1", store=store_path)
        rc = handle_archive_command(restore_args, out=out)
        assert rc == 0
        assert any("DB_HOST" in l for l in lines)

    def test_restore_missing_label_returns_error(self, store_path):
        lines, out = _out()
        args = Args(archive_cmd="restore", label="ghost", store=store_path)
        rc = handle_archive_command(args, out=out)
        assert rc == 1
        assert any("not found" in l for l in lines)

    def test_list_shows_labels(self, tmp_env, store_path):
        save_args = Args(archive_cmd="save", file=tmp_env, label="prod", store=store_path)
        handle_archive_command(save_args)
        lines, out = _out()
        list_args = Args(archive_cmd="list", store=store_path)
        rc = handle_archive_command(list_args, out=out)
        assert rc == 0
        assert any("prod" in l for l in lines)

    def test_list_empty_store(self, store_path):
        lines, out = _out()
        args = Args(archive_cmd="list", store=store_path)
        rc = handle_archive_command(args, out=out)
        assert rc == 0
        assert any("No archives" in l for l in lines)

    def test_delete_existing(self, tmp_env, store_path):
        save_args = Args(archive_cmd="save", file=tmp_env, label="v1", store=store_path)
        handle_archive_command(save_args)
        lines, out = _out()
        del_args = Args(archive_cmd="delete", label="v1", store=store_path)
        rc = handle_archive_command(del_args, out=out)
        assert rc == 0
        assert any("Deleted" in l for l in lines)

    def test_delete_nonexistent(self, store_path):
        lines, out = _out()
        args = Args(archive_cmd="delete", label="ghost", store=store_path)
        rc = handle_archive_command(args, out=out)
        assert rc == 1
