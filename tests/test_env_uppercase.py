import pytest
from envoy.env_uppercase import EnvUppercaser, UppercaseResult, UppercaseChange


@pytest.fixture
def uppercaser():
    return EnvUppercaser()


class TestUppercaseResult:
    def test_repr(self):
        r = UppercaseResult(
            changes=[UppercaseChange("db_host", "DB_HOST")],
            conflicts=[],
        )
        assert "UppercaseResult" in repr(r)
        assert "changes=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = UppercaseResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = UppercaseResult(changes=[UppercaseChange("foo", "FOO")])
        assert r.has_changes

    def test_has_conflicts_false_when_empty(self):
        r = UppercaseResult()
        assert not r.has_conflicts

    def test_has_conflicts_true_when_populated(self):
        r = UppercaseResult(conflicts=["FOO"])
        assert r.has_conflicts


class TestEnvUppercaser:
    def test_already_uppercase_no_changes(self, uppercaser):
        vars = {"HOST": "localhost", "PORT": "5432"}
        result = uppercaser.uppercase(vars)
        assert not result.has_changes
        assert result.vars == vars

    def test_lowercase_keys_uppercased(self, uppercaser):
        vars = {"host": "localhost", "port": "5432"}
        result = uppercaser.uppercase(vars)
        assert result.has_changes
        assert "HOST" in result.vars
        assert "PORT" in result.vars
        assert result.vars["HOST"] == "localhost"

    def test_mixed_case_keys_uppercased(self, uppercaser):
        vars = {"dbHost": "localhost", "DB_PORT": "5432"}
        result = uppercaser.uppercase(vars)
        assert "DBHOST" in result.vars
        assert "DB_PORT" in result.vars

    def test_conflict_detected_when_duplicate_after_uppercase(self, uppercaser):
        vars = {"foo": "lower", "FOO": "upper"}
        result = uppercaser.uppercase(vars)
        assert result.has_conflicts
        assert "FOO" in result.conflicts

    def test_change_records_original_and_new_key(self, uppercaser):
        vars = {"api_key": "secret"}
        result = uppercaser.uppercase(vars)
        assert len(result.changes) == 1
        change = result.changes[0]
        assert change.original_key == "api_key"
        assert change.new_key == "API_KEY"

    def test_empty_vars_returns_empty_result(self, uppercaser):
        result = uppercaser.uppercase({})
        assert not result.has_changes
        assert result.vars == {}
