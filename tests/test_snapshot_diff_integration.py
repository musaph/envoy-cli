"""Integration tests: SnapshotDiffer + EnvParser + Snapshot."""
import pytest
from envoy.parser import EnvParser
from envoy.snapshot import Snapshot
from envoy.env_snapshot_diff import SnapshotDiffer


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def differ():
    return SnapshotDiffer()


class TestSnapshotDiffWithParser:
    def test_parse_then_diff_detects_new_key(self, parser, differ):
        old_vars = parser.parse("A=1\nB=2\n")
        new_vars = parser.parse("A=1\nB=2\nC=3\n")
        old = Snapshot(vars=old_vars, label="old")
        new = Snapshot(vars=new_vars, label="new")
        result = differ.diff(old, new)
        assert len(result.added()) == 1
        assert result.added()[0].key == "C"

    def test_parse_then_diff_detects_removed_key(self, parser, differ):
        old_vars = parser.parse("A=1\nB=2\n")
        new_vars = parser.parse("A=1\n")
        old = Snapshot(vars=old_vars)
        new = Snapshot(vars=new_vars)
        result = differ.diff(old, new)
        assert len(result.removed()) == 1
        assert result.removed()[0].key == "B"

    def test_parse_then_diff_detects_value_change(self, parser, differ):
        old_vars = parser.parse("DB_URL=postgres://old\n")
        new_vars = parser.parse("DB_URL=postgres://new\n")
        old = Snapshot(vars=old_vars)
        new = Snapshot(vars=new_vars)
        result = differ.diff(old, new)
        assert len(result.changed()) == 1
        entry = result.changed()[0]
        assert entry.old_value == "postgres://old"
        assert entry.new_value == "postgres://new"

    def test_identical_parsed_envs_produce_no_diff(self, parser, differ):
        content = "FOO=bar\nBAZ=qux\n"
        vars_a = parser.parse(content)
        vars_b = parser.parse(content)
        snap_a = Snapshot(vars=vars_a)
        snap_b = Snapshot(vars=vars_b)
        result = differ.diff(snap_a, snap_b)
        assert not result.has_diff()
        assert len(result.unchanged()) == 2

    def test_checksum_changes_reflected_in_diff(self, parser, differ):
        old_vars = parser.parse("SECRET=abc\n")
        new_vars = parser.parse("SECRET=xyz\n")
        old = Snapshot(vars=old_vars)
        new = Snapshot(vars=new_vars)
        assert old.checksum != new.checksum
        result = differ.diff(old, new)
        assert result.has_diff()
