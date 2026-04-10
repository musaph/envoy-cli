"""Tests for EnvPatcher patch generation and application."""
import pytest
from envoy.env_diff_patch import EnvPatch, EnvPatcher, PatchOperation


@pytest.fixture
def patcher():
    return EnvPatcher()


class TestPatchOperation:
    def test_to_dict_add(self):
        op = PatchOperation(op="add", key="FOO", new_value="bar")
        d = op.to_dict()
        assert d == {"op": "add", "key": "FOO", "new_value": "bar"}

    def test_to_dict_remove(self):
        op = PatchOperation(op="remove", key="FOO", old_value="bar")
        d = op.to_dict()
        assert d == {"op": "remove", "key": "FOO", "old_value": "bar"}

    def test_roundtrip(self):
        op = PatchOperation(op="replace", key="X", old_value="1", new_value="2")
        assert PatchOperation.from_dict(op.to_dict()) == op

    def test_repr(self):
        op = PatchOperation(op="add", key="KEY")
        assert "add" in repr(op) and "KEY" in repr(op)


class TestEnvPatch:
    def test_is_empty_true(self):
        patch = EnvPatch()
        assert patch.is_empty()

    def test_is_empty_false(self):
        patch = EnvPatch(operations=[PatchOperation(op="add", key="A", new_value="1")])
        assert not patch.is_empty()

    def test_to_dict_roundtrip(self):
        patch = EnvPatch(
            operations=[
                PatchOperation(op="add", key="A", new_value="1"),
                PatchOperation(op="remove", key="B", old_value="2"),
            ]
        )
        restored = EnvPatch.from_dict(patch.to_dict())
        assert len(restored.operations) == 2
        assert restored.operations[0].key == "A"


class TestEnvPatcher:
    def test_generate_no_changes(self, patcher):
        base = {"A": "1", "B": "2"}
        patch = patcher.generate(base, base.copy())
        assert patch.is_empty()

    def test_generate_add(self, patcher):
        patch = patcher.generate({"A": "1"}, {"A": "1", "B": "2"})
        assert len(patch.operations) == 1
        assert patch.operations[0].op == "add"
        assert patch.operations[0].key == "B"

    def test_generate_remove(self, patcher):
        patch = patcher.generate({"A": "1", "B": "2"}, {"A": "1"})
        assert len(patch.operations) == 1
        assert patch.operations[0].op == "remove"
        assert patch.operations[0].key == "B"

    def test_generate_replace(self, patcher):
        patch = patcher.generate({"A": "old"}, {"A": "new"})
        assert patch.operations[0].op == "replace"
        assert patch.operations[0].old_value == "old"
        assert patch.operations[0].new_value == "new"

    def test_apply_add(self, patcher):
        patch = patcher.generate({}, {"X": "1"})
        result, conflicts = patcher.apply({}, patch)
        assert result == {"X": "1"}
        assert conflicts == []

    def test_apply_remove(self, patcher):
        patch = patcher.generate({"X": "1"}, {})
        result, conflicts = patcher.apply({"X": "1"}, patch)
        assert "X" not in result
        assert conflicts == []

    def test_apply_replace(self, patcher):
        patch = patcher.generate({"X": "old"}, {"X": "new"})
        result, conflicts = patcher.apply({"X": "old"}, patch)
        assert result["X"] == "new"

    def test_apply_conflict_on_add(self, patcher):
        patch = EnvPatch(operations=[PatchOperation(op="add", key="X", new_value="1")])
        _, conflicts = patcher.apply({"X": "existing"}, patch)
        assert "X" in conflicts

    def test_apply_conflict_on_replace_mismatch(self, patcher):
        patch = EnvPatch(
            operations=[PatchOperation(op="replace", key="X", old_value="expected", new_value="new")]
        )
        _, conflicts = patcher.apply({"X": "different"}, patch)
        assert "X" in conflicts

    def test_roundtrip_generate_and_apply(self, patcher):
        base = {"A": "1", "B": "2", "C": "3"}
        target = {"A": "1", "B": "updated", "D": "4"}
        patch = patcher.generate(base, target)
        result, conflicts = patcher.apply(base, patch)
        assert result == target
        assert conflicts == []
