"""Tests for envoy.env_alias module."""
import pytest
from envoy.env_alias import AliasEntry, AliasResult, EnvAliasManager


@pytest.fixture
def manager() -> EnvAliasManager:
    return EnvAliasManager()


class TestAliasEntry:
    def test_to_dict_roundtrip(self):
        entry = AliasEntry(canonical="DATABASE_URL", aliases=["DB_URL", "DB_URI"])
        data = entry.to_dict()
        restored = AliasEntry.from_dict(data)
        assert restored.canonical == entry.canonical
        assert restored.aliases == entry.aliases

    def test_repr_contains_canonical(self):
        entry = AliasEntry(canonical="API_KEY", aliases=["TOKEN"])
        assert "API_KEY" in repr(entry)

    def test_from_dict_missing_aliases_defaults_empty(self):
        entry = AliasEntry.from_dict({"canonical": "FOO"})
        assert entry.aliases == []


class TestAliasResult:
    def test_repr_shows_counts(self):
        result = AliasResult(resolved={"A": "1"}, unresolved=["B", "C"])
        r = repr(result)
        assert "1" in r
        assert "2" in r


class TestEnvAliasManager:
    def test_register_stores_entry(self, manager):
        entry = manager.register("DATABASE_URL", ["DB_URL", "DB_URI"])
        assert entry.canonical == "DATABASE_URL"
        assert "DB_URL" in entry.aliases

    def test_resolve_canonical_returns_itself(self, manager):
        manager.register("DATABASE_URL", ["DB_URL"])
        assert manager.resolve("DATABASE_URL") == "DATABASE_URL"

    def test_resolve_alias_returns_canonical(self, manager):
        manager.register("DATABASE_URL", ["DB_URL", "DB_URI"])
        assert manager.resolve("DB_URL") == "DATABASE_URL"
        assert manager.resolve("DB_URI") == "DATABASE_URL"

    def test_resolve_unknown_key_returns_none(self, manager):
        assert manager.resolve("UNKNOWN_KEY") is None

    def test_expand_resolves_aliases(self, manager):
        manager.register("DATABASE_URL", ["DB_URL"])
        manager.register("API_KEY", ["TOKEN"])
        result = manager.expand({"DB_URL": "postgres://localhost", "TOKEN": "abc123"})
        assert result.resolved["DATABASE_URL"] == "postgres://localhost"
        assert result.resolved["API_KEY"] == "abc123"
        assert result.unresolved == []

    def test_expand_unresolved_keys_reported(self, manager):
        manager.register("DATABASE_URL", ["DB_URL"])
        result = manager.expand({"DB_URL": "postgres://", "MYSTERY_VAR": "x"})
        assert "DATABASE_URL" in result.resolved
        assert "MYSTERY_VAR" in result.unresolved

    def test_expand_canonical_key_directly(self, manager):
        manager.register("PORT", ["APP_PORT"])
        result = manager.expand({"PORT": "8080"})
        assert result.resolved["PORT"] == "8080"
        assert result.unresolved == []

    def test_list_entries_returns_all(self, manager):
        manager.register("A", ["a1"])
        manager.register("B", ["b1", "b2"])
        entries = manager.list_entries()
        canonicals = {e.canonical for e in entries}
        assert canonicals == {"A", "B"}
