"""Tests for envoy.env_namespace."""
import pytest
from envoy.env_namespace import EnvNamespaceManager, NamespaceResult


@pytest.fixture
def manager():
    return EnvNamespaceManager()


@pytest.fixture
def sample_vars():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "AWS_ACCESS_KEY": "AKIA123",
        "AWS_SECRET_KEY": "secret",
        "APP_ENV": "production",
        "DEBUG": "false",
    }


class TestNamespaceResult:
    def test_repr(self):
        r = NamespaceResult(namespace="DB", vars={"DB_HOST": "localhost"})
        assert "DB" in repr(r)
        assert "count=1" in repr(r)

    def test_defaults_are_empty(self):
        r = NamespaceResult(namespace="X")
        assert r.vars == {}
        assert r.stripped == {}


class TestEnvNamespaceManager:
    def test_list_namespaces(self, manager, sample_vars):
        ns = manager.list_namespaces(sample_vars)
        assert "DB" in ns
        assert "AWS" in ns
        assert "APP" in ns
        assert "DEBUG" not in ns  # no separator

    def test_list_namespaces_sorted(self, manager, sample_vars):
        ns = manager.list_namespaces(sample_vars)
        assert ns == sorted(ns)

    def test_extract_db_namespace(self, manager, sample_vars):
        result = manager.extract(sample_vars, "DB")
        assert result.namespace == "DB"
        assert "DB_HOST" in result.vars
        assert "DB_PORT" in result.vars
        assert "AWS_ACCESS_KEY" not in result.vars

    def test_extract_stripped_keys(self, manager, sample_vars):
        result = manager.extract(sample_vars, "DB")
        assert "HOST" in result.stripped
        assert "PORT" in result.stripped
        assert result.stripped["HOST"] == "localhost"

    def test_extract_empty_namespace(self, manager, sample_vars):
        result = manager.extract(sample_vars, "NONEXISTENT")
        assert result.vars == {}
        assert result.stripped == {}

    def test_extract_case_insensitive_prefix(self, manager, sample_vars):
        result = manager.extract(sample_vars, "db")
        assert "DB_HOST" in result.vars

    def test_inject_adds_prefixed_vars(self, manager, sample_vars):
        updated = manager.inject(sample_vars, "DB", {"PASSWORD": "secret"})
        assert "DB_PASSWORD" in updated
        assert updated["DB_PASSWORD"] == "secret"
        # original vars preserved
        assert "DB_HOST" in updated

    def test_inject_does_not_mutate_original(self, manager, sample_vars):
        original_keys = set(sample_vars.keys())
        manager.inject(sample_vars, "DB", {"PASSWORD": "secret"})
        assert set(sample_vars.keys()) == original_keys

    def test_remove_namespace(self, manager, sample_vars):
        updated = manager.remove_namespace(sample_vars, "DB")
        assert "DB_HOST" not in updated
        assert "DB_PORT" not in updated
        assert "AWS_ACCESS_KEY" in updated
        assert "DEBUG" in updated

    def test_remove_nonexistent_namespace_unchanged(self, manager, sample_vars):
        updated = manager.remove_namespace(sample_vars, "GHOST")
        assert updated == sample_vars

    def test_list_no_namespaces_when_no_separators(self, manager):
        flat = {"FOO": "1", "BAR": "2"}
        assert manager.list_namespaces(flat) == []
