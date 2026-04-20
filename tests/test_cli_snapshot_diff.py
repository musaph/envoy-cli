"""Tests for cli_snapshot_diff module."""
import json
import io
import pytest
from pathlib import Path
from envoy.snapshot import Snapshot
from envoy.cli_snapshot_diff import handle_snapshot_diff_command


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def old_file(tmp_dir):
    snap = Snapshot(vars={"A": "1", "B": "old"}, label="v1")
    p = tmp_dir / "old.json"
    p.write_text(json.dumps(snap.to_dict()))
    return p


@pytest.fixture
def new_file(tmp_dir):
    snap = Snapshot(vars={"A": "1", "B": "new", "C": "added"}, label="v2")
    p = tmp_dir / "new.json"
    p.write_text(json.dumps(snap.to_dict()))
    return p


def _out():
    return io.StringIO()


class TestHandleSnapshotDiffCommand:
    def test_no_subcommand_shows_usage(self):
        buf = _out()
        args = Args(snapshot_diff_cmd=None)
        rc = handle_snapshot_diff_command(args, out=buf)
        assert rc == 1
        assert "Usage" in buf.getvalue()

    def test_missing_old_file_returns_error(self, tmp_dir, new_file):
        buf = _out()
        args = Args(
            snapshot_diff_cmd="compare",
            old=str(tmp_dir / "missing.json"),
            new=str(new_file),
            show_unchanged=False,
        )
        rc = handle_snapshot_diff_command(args, out=buf)
        assert rc == 1
        assert "not found" in buf.getvalue()

    def test_compare_shows_added_removed_changed(self, old_file, new_file):
        buf = _out()
        args = Args(
            snapshot_diff_cmd="compare",
            old=str(old_file),
            new=str(new_file),
            show_unchanged=False,
        )
        rc = handle_snapshot_diff_command(args, out=buf)
        assert rc == 0
        output = buf.getvalue()
        assert "+ C" in output
        assert "~ B" in output
        assert "Added: 1" in output
        assert "Changed: 1" in output

    def test_show_unchanged_flag_includes_unchanged_keys(self, old_file, new_file):
        buf = _out()
        args = Args(
            snapshot_diff_cmd="compare",
            old=str(old_file),
            new=str(new_file),
            show_unchanged=True,
        )
        rc = handle_snapshot_diff_command(args, out=buf)
        assert rc == 0
        assert "A=1" in buf.getvalue()

    def test_identical_snapshots_no_diff_output(self, tmp_dir):
        snap = Snapshot(vars={"X": "1"}, label="same")
        p1 = tmp_dir / "s1.json"
        p2 = tmp_dir / "s2.json"
        p1.write_text(json.dumps(snap.to_dict()))
        p2.write_text(json.dumps(snap.to_dict()))
        buf = _out()
        args = Args(
            snapshot_diff_cmd="compare",
            old=str(p1),
            new=str(p2),
            show_unchanged=False,
        )
        rc = handle_snapshot_diff_command(args, out=buf)
        assert rc == 0
        assert "Added: 0" in buf.getvalue()
