"""Tests for EnvIndexer and related types."""
import pytest
from envoy.env_index import EnvIndexer, IndexEntry, IndexResult


@pytest.fixture
def indexer():
    return EnvIndexer()


@pytest.fixture
def sample_vars():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "envoy",
        "SECRET_KEY": "",
        "PLAIN": "value",
    }


class TestIndexEntry:
    def test_repr_contains_key(self):
        e = IndexEntry(key="FOO", position=0, value_length=3, is_empty=False, prefix="FOO")
        assert "FOO" in repr(e)

    def test_to_dict_roundtrip(self):
        e = IndexEntry(key="DB_HOST", position=1, value_length=9, is_empty=False, prefix="DB")
        restored = IndexEntry.from_dict(e.to_dict())
        assert restored.key == e.key
        assert restored.position == e.position
        assert restored.prefix == e.prefix

    def test_from_dict_missing_prefix_defaults_none(self):
        data = {"key": "X", "position": 0, "value_length": 1, "is_empty": False}
        e = IndexEntry.from_dict(data)
        assert e.prefix is None


class TestIndexResult:
    def test_repr_contains_count(self):
        r = IndexResult(entries=[])
        assert "0" in repr(r)

    def test_keys_returns_all_keys(self, indexer, sample_vars):
        result = indexer.build(sample_vars)
        assert set(result.keys) == set(sample_vars.keys())

    def test_empty_keys_identified(self, indexer, sample_vars):
        result = indexer.build(sample_vars)
        assert "SECRET_KEY" in result.empty_keys
        assert "DB_HOST" not in result.empty_keys

    def test_by_prefix_filters(self, indexer, sample_vars):
        result = indexer.build(sample_vars)
        db_entries = result.by_prefix("DB")
        assert all(e.prefix == "DB" for e in db_entries)
        assert len(db_entries) == 2

    def test_get_existing_key(self, indexer, sample_vars):
        result = indexer.build(sample_vars)
        entry = result.get("APP_NAME")
        assert entry is.key == "APP_NAME"

    def test_get_missing_key_returns_none(self, indexer, sample_vars):
        result = indexer.build(sample_vars)
        assertEXISTENT") is None


class TestEnvIndexer:
    def test_positions_are_sequential(self, indexer, sample_vars):
        result = indexer.build(sample_vars)
        positions = [e.position for e in result.entries]
        assert positions == list(range(len(sample_vars)))

    def test_value_length_correct(self, indexer):
        result = indexer.build({"KEY": "hello"})
        assert result.entries[0].value_length == 5

    def test_no_prefix_for_key_without_separator(self, indexer):
        result = indexer.build({"PLAIN": "x"})
        assert result.entries[0].prefix is None

    def test_custom_separator(self):
        indexer = EnvIndexer(prefix_separator=".")
        result = indexer.build({"app.name": "envoy"})
        assert result.entries[0].prefix == "app"

    def test_empty_vars_produces_empty_result(self, indexer):
        result = indexer.build({})
        assert result.entries == []
