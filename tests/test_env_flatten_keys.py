"""Tests for EnvKeyFlattener."""
import pytest
from envoy.env_flatten_keys import EnvKeyFlattener, FlattenKeyChange, FlattenKeyResult


@pytest.fixture
def flattener():
    return EnvKeyFlattener()


@pytest.fixture
def overwrite_flattener():
    return EnvKeyFlattener(overwrite=True)


@pytest.fixture
def sample_vars():
    return {
        "APP__DB__HOST": "localhost",
        "APP__DB__PORT": "5432",
        "PLAIN_KEY": "value",
     TestFlattenKeyResult:
    def test_repr(self):
        r = FlattenKeyResult(vars={}, changes=[], skipped=[])
        assert "FlattenKeyResult" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = FlattenKeyResult(vars={}, changes=[], skipped=[])
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = FlattenKeyResult(
            vars={},
            changes=[FlattenKeyChange("A__B", "A_B")],
            skipped=[],
        )
        assert r.has_changes

    def test_changed_keys_lists_originals(self):
        r = FlattenKeyResult(
            vars={},
            changes=[FlattenKeyChange("A__B", "A_B"), FlattenKeyChange("C__D", "C_D")],
            skipped=[],
        )
        assert r.changed_keys == ["A__B", "C__D"]


class TestEnvKeyFlattener:
    def test_no_double_underscore_unchanged(self, flattener):
        vars_ = {"PLAIN_KEY": "value", "ANOTHER": "x"}
        result = flattener.flatten(vars_)
        assert not result.has_changes
        assert result.vars == vars_

    def test_flattens_double_underscore(self, flattener, sample_vars):
        result = flattener.flatten(sample_vars)
        assert "APP_DB_HOST" in result.vars
        assert "APP_DB_PORT" in result.vars
        assert result.vars["APP_DB_HOST"] == "localhost"

    def test_plain_keys_preserved(self, flattener, sample_vars):
        result = flattener.flatten(sample_vars)
        assert "PLAIN_KEY" in result.vars
        assert result.vars["PLAIN_KEY"] == "value"

    def test_original_keys_removed(self, flattener, sample_vars):
        result = flattener.flatten(sample_vars)
        assert "APP__DB__HOST" not in result.vars
        assert "APP__DB__PORT" not in result.vars

    def test_change_records_correct(self, flattener):
        result = flattener.flatten({"X__Y": "1"})
        assert len(result.changes) == 1
        assert result.changes[0].original == "X__Y"
        assert result.changes[0].flattened == "X_Y"

    def test_conflict_skipped_without_overwrite(self, flattener):
        vars_ = {"A__B": "nested", "A_B": "existing"}
        result = flattener.flatten(vars_)
        assert "A__B" in result.skipped
        assert result.vars["A_B"] == "existing"

    def test_conflict_overwritten_with_overwrite(self, overwrite_flattener):
        vars_ = {"A__B": "nested", "A_B": "existing"}
        result = overwrite_flattener.flatten(vars_)
        assert result.vars["A_B"] == "nested"
        assert "A__B" not in result.skipped

    def test_custom_separator(self):
        f = EnvKeyFlattener(separator=".", replacement="_")
        result = f.flatten({"APP.DB.HOST": "localhost"})
        assert "APP_DB_HOST" in result.vars

    def test_change_repr(self):
        c = FlattenKeyChange("A__B", "A_B")
        assert "A__B" in repr(c)
        assert "A_B" in repr(c)
