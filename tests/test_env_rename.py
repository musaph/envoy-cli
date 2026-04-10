"""Tests for envoy.env_rename."""
import pytest
from envoy.env_rename import EnvRenamer, RenameOperation, RenameResult


@pytest.fixture
def renamer():
    return EnvRenamer()


@pytest.fixture
def base_vars():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_SECRET": "abc123"}


class TestRenameOperation:
    def test_to_dict_roundtrip(self):
        op = RenameOperation(old_key="FOO", new_key="BAR", value="hello")
        assert RenameOperation.from_dict(op.to_dict()) == op

    def test_repr_contains_keys(self):
        op = RenameOperation(old_key="OLD", new_key="NEW")
        assert "OLD" in repr(op)
        assert "NEW" in repr(op)


class TestRenameResult:
    def test_success_when_no_skipped(self):
        result = RenameResult(applied=[RenameOperation("A", "B")], skipped=[], vars={})
        assert result.success is True

    def test_not_success_when_skipped(self):
        result = RenameResult(applied=[], skipped=[("X", "key not found")], vars={})
        assert result.success is False

    def test_repr_contains_counts(self):
        result = RenameResult(
            applied=[RenameOperation("A", "B")],
            skipped=[("C", "reason")],
            vars={},
        )
        assert "applied=1" in repr(result)
        assert "skipped=1" in repr(result)


class TestEnvRenamer:
    def test_simple_rename(self, renamer, base_vars):
        ops = [RenameOperation(old_key="DB_HOST", new_key="DATABASE_HOST")]
        result = renamer.rename(base_vars, ops)
        assert result.success
        assert "DATABASE_HOST" in result.vars
        assert "DB_HOST" not in result.vars
        assert result.vars["DATABASE_HOST"] == "localhost"

    def test_old_key_not_found_is_skipped(self, renamer, base_vars):
        ops = [RenameOperation(old_key="MISSING_KEY", new_key="NEW_KEY")]
        result = renamer.rename(base_vars, ops)
        assert not result.success
        assert len(result.skipped) == 1
        assert result.skipped[0][1] == "key not found"

    def test_target_key_exists_without_overwrite_is_skipped(self, renamer, base_vars):
        ops = [RenameOperation(old_key="DB_HOST", new_key="DB_PORT")]
        result = renamer.rename(base_vars, ops)
        assert not result.success
        assert result.skipped[0][1] == "target key already exists"
        assert result.vars["DB_HOST"] == "localhost"  # unchanged

    def test_target_key_exists_with_overwrite(self, renamer, base_vars):
        ops = [RenameOperation(old_key="DB_HOST", new_key="DB_PORT")]
        result = renamer.rename(base_vars, ops, overwrite=True)
        assert result.success
        assert result.vars["DB_PORT"] == "localhost"
        assert "DB_HOST" not in result.vars

    def test_identical_old_and_new_key_is_skipped(self, renamer, base_vars):
        ops = [RenameOperation(old_key="DB_HOST", new_key="DB_HOST")]
        result = renamer.rename(base_vars, ops)
        assert not result.success
        assert result.skipped[0][1] == "old and new key are identical"

    def test_multiple_operations(self, renamer, base_vars):
        ops = [
            RenameOperation(old_key="DB_HOST", new_key="DATABASE_HOST"),
            RenameOperation(old_key="DB_PORT", new_key="DATABASE_PORT"),
        ]
        result = renamer.rename(base_vars, ops)
        assert result.success
        assert len(result.applied) == 2
        assert "DATABASE_HOST" in result.vars
        assert "DATABASE_PORT" in result.vars

    def test_build_operations_from_pairs(self, renamer):
        pairs = [("OLD_A", "NEW_A"), ("OLD_B", "NEW_B")]
        ops = renamer.build_operations(pairs)
        assert len(ops) == 2
        assert ops[0].old_key == "OLD_A"
        assert ops[1].new_key == "NEW_B"

    def test_original_vars_not_mutated(self, renamer, base_vars):
        original = dict(base_vars)
        ops = [RenameOperation(old_key="DB_HOST", new_key="DATABASE_HOST")]
        renamer.rename(base_vars, ops)
        assert base_vars == original
