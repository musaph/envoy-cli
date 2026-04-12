"""Tests for envoy.env_clone."""
import pytest
from envoy.env_clone import CloneResult, EnvCloner


@pytest.fixture
def cloner() -> EnvCloner:
    return EnvCloner()


@pytest.fixture
def sample_vars() -> dict:
    return {
        "APP_HOST": "localhost",
        "APP_PORT": "8080",
        "DB_URL": "postgres://localhost/dev",
        "SECRET_KEY": "abc123",
    }


class TestCloneResult:
    def test_repr(self):
        r = CloneResult(cloned={"A": "1"}, skipped=["B"], renamed={"C": "D"})
        assert "cloned=1" in repr(r)
        assert "skipped=1" in repr(r)
        assert "renamed=1" in repr(r)

    def test_has_renames_false_when_empty(self):
        r = CloneResult()
        assert r.has_renames is False

    def test_has_renames_true_when_populated(self):
        r = CloneResult(renamed={"OLD": "NEW"})
        assert r.has_renames is True


class TestEnvCloner:
    def test_plain_clone_copies_all(self, cloner, sample_vars):
        result = cloner.clone(sample_vars)
        assert result.cloned == sample_vars
        assert result.skipped == []
        assert result.renamed == {}

    def test_skip_keys_excludes_entries(self, sample_vars):
        c = EnvCloner(skip_keys=["SECRET_KEY"])
        result = c.clone(sample_vars)
        assert "SECRET_KEY" not in result.cloned
        assert "SECRET_KEY" in result.skipped

    def test_strip_prefix_removes_prefix(self, sample_vars):
        c = EnvCloner(strip_prefix="APP_")
        result = c.clone(sample_vars)
        assert "HOST" in result.cloned
        assert "PORT" in result.cloned
        # Keys without the prefix are unchanged
        assert "DB_URL" in result.cloned

    def test_add_prefix_prepends_to_all_keys(self, sample_vars):
        c = EnvCloner(add_prefix="CLONE_")
        result = c.clone(sample_vars)
        for key in result.cloned:
            assert key.startswith("CLONE_")

    def test_strip_then_add_prefix(self):
        vars = {"OLD_FOO": "bar", "OLD_BAZ": "qux"}
        c = EnvCloner(strip_prefix="OLD_", add_prefix="NEW_")
        result = c.clone(vars)
        assert "NEW_FOO" in result.cloned
        assert "NEW_BAZ" in result.cloned
        assert result.cloned["NEW_FOO"] == "bar"

    def test_rename_map_renames_key(self):
        vars = {"HOST": "localhost", "PORT": "5432"}
        c = EnvCloner(rename_map={"HOST": "DATABASE_HOST"})
        result = c.clone(vars)
        assert "DATABASE_HOST" in result.cloned
        assert "HOST" not in result.cloned
        assert result.renamed == {"HOST": "DATABASE_HOST"}

    def test_rename_applied_after_strip_prefix(self):
        vars = {"APP_HOST": "localhost"}
        c = EnvCloner(strip_prefix="APP_", rename_map={"HOST": "SERVER_HOST"})
        result = c.clone(vars)
        assert "SERVER_HOST" in result.cloned
        assert result.renamed == {"HOST": "SERVER_HOST"}

    def test_values_are_deep_copied(self, cloner, sample_vars):
        result = cloner.clone(sample_vars)
        result.cloned["APP_HOST"] = "changed"
        assert sample_vars["APP_HOST"] == "localhost"

    def test_empty_vars_returns_empty_result(self, cloner):
        result = cloner.clone({})
        assert result.cloned == {}
        assert result.skipped == []
