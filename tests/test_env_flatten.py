"""Tests for envoy.env_flatten."""
from __future__ import annotations

import json
import pytest

from envoy.env_flatten import EnvFlattener, FlattenResult, FlattenChange


@pytest.fixture
def flattener() -> EnvFlattener:
    return EnvFlattener()


@pytest.fixture
def sample_vars():
    return {
        "PLAIN": "hello",
        "DB": json.dumps({"host": "localhost", "port": "5432"}),
        "NESTED": json.dumps({"a": {"b": "deep"}}),
    }


class TestFlattenResult:
    def test_repr(self):
        r = FlattenResult(changes=[FlattenChange("K", "K.x", "v")], skipped=["Z"])
        assert "changes=1" in repr(r)
        assert "skipped=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = FlattenResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = FlattenResult(changes=[FlattenChange("K", "K.x", "v")])
        assert r.has_changes


class TestEnvFlattener:
    def test_plain_var_is_skipped(self, flattener):
        result = flattener.flatten({"FOO": "bar"})
        assert "FOO" in result.flattened
        assert result.flattened["FOO"] == "bar"
        assert "FOO" in result.skipped
        assert not result.has_changes

    def test_json_object_is_expanded(self, flattener):
        result = flattener.flatten({"DB": json.dumps({"host": "localhost"})})
        assert "DB.host" in result.flattened
        assert result.flattened["DB.host"] == "localhost"
        assert result.has_changes

    def test_original_key_removed_after_expansion(self, flattener):
        result = flattener.flatten({"DB": json.dumps({"host": "localhost"})})
        assert "DB" not in result.flattened

    def test_nested_json_expanded_deeply(self, flattener):
        result = flattener.flatten({"X": json.dumps({"a": {"b": "deep"}})})
        assert "X.a.b" in result.flattened
        assert result.flattened["X.a.b"] == "deep"

    def test_custom_separator(self):
        f = EnvFlattener(separator="__")
        result = f.flatten({"DB": json.dumps({"host": "localhost"})})
        assert "DB__host" in result.flattened

    def test_invalid_json_string_is_skipped(self, flattener):
        result = flattener.flatten({"BAD": "{not valid json"})
        assert "BAD" in result.skipped
        assert result.flattened["BAD"] == "{not valid json"

    def test_json_array_is_skipped(self, flattener):
        result = flattener.flatten({"ARR": "[1,2,3]"})
        assert "ARR" in result.skipped

    def test_mixed_vars(self, flattener, sample_vars):
        result = flattener.flatten(sample_vars)
        assert "PLAIN" in result.skipped
        assert "DB.host" in result.flattened
        assert "DB.port" in result.flattened
        assert "NESTED.a.b" in result.flattened

    def test_change_records_original_and_derived(self, flattener):
        result = flattener.flatten({"S": json.dumps({"k": "v"})})
        assert len(result.changes) == 1
        ch = result.changes[0]
        assert ch.original_key == "S"
        assert ch.derived_key == "S.k"
        assert ch.value == "v"

    def test_numeric_values_converted_to_str(self, flattener):
        result = flattener.flatten({"CFG": json.dumps({"retries": 3})})
        assert result.flattened["CFG.retries"] == "3"
