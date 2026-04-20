"""Tests for EnvDiffKeys and cli_diff_keys."""
import pytest
from unittest.mock import patch, mock_open

from envoy.env_diff_keys import DiffKeysEntry, DiffKeysResult, EnvDiffKeys
from envoy.cli_diff_keys import handle_diff_keys_command


@pytest.fixture
def differ():
    return EnvDiffKeys()


@pytest.fixture
def old_vars():
    return {"HOST": "localhost", "PORT": "5432", "DB": "mydb"}


@pytest.fixture
def new_vars():
    return {"HOST": "prod.host", "PORT": "5432", "USER": "admin"}


class TestDiffKeysResult:
    def test_repr(self):
        r = DiffKeysResult(added=["A"], removed=["B"], common=["C", "D"])
        assert "added=1" in repr(r)
        assert "removed=1" in repr(r)
        assert "common=2" in repr(r)

    def test_has_diff_true_when_added(self):
        r = DiffKeysResult(added=["NEW"])
        assert r.has_diff is True

    def test_has_diff_true_when_removed(self):
        r = DiffKeysResult(removed=["OLD"])
        assert r.has_diff is True

    def test_has_diff_false_when_only_common(self):
        r = DiffKeysResult(common=["A", "B"])
        assert r.has_diff is False

    def test_entries_sorted_by_status_and_key(self):
        r = DiffKeysResult(added=["Z", "A"], removed=["M"], common=["C"])
        statuses = [e.status for e in r.entries]
        assert statuses.index("added") < statuses.index("common")


class TestEnvDiffKeys:
    def test_compare_identical(self, differ):
        v = {"A": "1", "B": "2"}
        result = differ.compare(v, v)
        assert result.added == []
        assert result.removed == []
        assert sorted(result.common) == ["A", "B"]

    def test_compare_added_keys(self, differ, old_vars, new_vars):
        result = differ.compare(old_vars, new_vars)
        assert "USER" in result.added
        assert "DB" in result.removed
        assert "HOST" in result.common
        assert "PORT" in result.common

    def test_compare_empty_old(self, differ):
        result = differ.compare({}, {"A": "1"})
        assert result.added == ["A"]
        assert result.removed == []

    def test_compare_empty_new(self, differ):
        result = differ.compare({"A": "1"}, {})
        assert result.removed == ["A"]
        assert result.added == []

    def test_only_in_old(self, differ, old_vars, new_vars):
        result = differ.only_in_old(old_vars, new_vars)
        assert "DB" in result
        assert "HOST" not in result

    def test_only_in_new(self, differ, old_vars, new_vars):
        result = differ.only_in_new(old_vars, new_vars)
        assert "USER" in result
        assert "PORT" not in result


class TestHandleDiffKeysCommand:
    class Args:
        def __init__(self, old, new, only_added=False, only_removed=False, no_common=False):
            self.old = old
            self.new = new
            self.only_added = only_added
            self.only_removed = only_removed
            self.no_common = no_common

    def test_no_old_attr_shows_usage(self):
        class Empty:
            pass
        out = []
        rc = handle_diff_keys_command(Empty(), out.append)
        assert rc == 1
        assert any("Usage" in line for line in out)

    def test_missing_old_file_returns_error(self, tmp_path):
        args = self.Args(str(tmp_path / "missing.env"), str(tmp_path / "b.env"))
        out = []
        rc = handle_diff_keys_command(args, out.append)
        assert rc == 1
        assert any("not found" in line for line in out)

    def test_missing_new_file_returns_error(self, tmp_path):
        old = tmp_path / "old.env"
        old.write_text("A=1\n")
        args = self.Args(str(old), str(tmp_path / "missing.env"))
        out = []
        rc = handle_diff_keys_command(args, out.append)
        assert rc == 1
        assert any("not found" in line for line in out)

    def test_shows_added_and_removed(self, tmp_path):
        old = tmp_path / "old.env"
        new = tmp_path / "new.env"
        old.write_text("HOST=localhost\nDB=mydb\n")
        new.write_text("HOST=prod\nUSER=admin\n")
        args = self.Args(str(old), str(new), no_common=True)
        out = []
        rc = handle_diff_keys_command(args, out.append)
        assert rc == 0
        combined = "\n".join(out)
        assert "+ USER" in combined
        assert "- DB" in combined
