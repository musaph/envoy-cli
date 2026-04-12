"""Tests for envoy.env_uppercase."""
import pytest
from envoy.env_uppercase import EnvUppercaser, UppercaseChange, UppercaseResult


@pytest.fixture
def uppercaser():
    return EnvUppercaser()


# ---------------------------------------------------------------------------
# UppercaseResult helpers
# ---------------------------------------------------------------------------

class TestUppercaseResult:
    def test_repr(self):
        r = UppercaseResult(changes=[UppercaseChange("a", "A")], conflicts=[])
        assert "changes=1" in repr(r)
        assert "conflicts=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = UppercaseResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = UppercaseResult(changes=[UppercaseChange("x", "X")])
        assert r.has_changes

    def test_has_conflicts_false_when_empty(self):
        assert not UppercaseResult().has_conflicts

    def test_has_conflicts_true_when_populated(self):
        r = UppercaseResult(conflicts=[("db_host", "DB_HOST")])
        assert r.has_conflicts


class TestUppercaseChange:
    def test_repr_contains_keys(self):
        c = UppercaseChange("foo", "FOO")
        assert "foo" in repr(c)
        assert "FOO" in repr(c)


# ---------------------------------------------------------------------------
# EnvUppercaser.normalize
# ---------------------------------------------------------------------------

class TestEnvUppercaser:
    def test_already_uppercase_no_changes(self, uppercaser):
        vars = {"HOST": "localhost", "PORT": "5432"}
        result = uppercaser.normalize(vars)
        assert result.vars == vars
        assert not result.has_changes
        assert not result.has_conflicts

    def test_lowercase_keys_are_uppercased(self, uppercaser):
        result = uppercaser.normalize({"host": "localhost", "port": "5432"})
        assert result.vars == {"HOST": "localhost", "PORT": "5432"}
        assert len(result.changes) == 2

    def test_mixed_case_keys_normalized(self, uppercaser):
        result = uppercaser.normalize({"Database_Host": "db"})
        assert "DATABASE_HOST" in result.vars
        assert result.has_changes

    def test_empty_dict_returns_empty_result(self, uppercaser):
        result = uppercaser.normalize({})
        assert result.vars == {}
        assert not result.has_changes
        assert not result.has_conflicts

    def test_collision_detected_last_value_wins(self, uppercaser):
        # Python dicts preserve insertion order; 'DB_HOST' comes last
        vars = {"db_host": "first", "DB_HOST": "second"}
        result = uppercaser.normalize(vars)
        assert result.vars["DB_HOST"] == "second"
        assert result.has_conflicts
        assert len(result.conflicts) == 1

    def test_change_records_original_and_normalized(self, uppercaser):
        result = uppercaser.normalize({"api_key": "secret"})
        assert any(c.original == "api_key" and c.normalized == "API_KEY"
                   for c in result.changes)

    def test_values_are_preserved_unchanged(self, uppercaser):
        result = uppercaser.normalize({"key": "hello world"})
        assert result.vars["KEY"] == "hello world"
