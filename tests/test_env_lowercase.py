import pytest
from envoy.env_lowercase import EnvLowercaser, LowercaseChange, LowercaseResult


@pytest.fixture
def lowercaser():
    return EnvLowercaser()


@pytest.fixture
def overwrite_lowercaser():
    return EnvLowercaser(overwrite=True)


@pytest.fixture
def sample_vars():
    return {"DB_HOST": "localhost", "API_KEY": "secret", "port": "5432"}


class TestLowercaseResult:
    def test_repr(self):
        r = LowercaseResult(changes=[LowercaseChange("db_host", "DB_HOST", "localhost")], vars={"db_host": "localhost"})
        assert "LowercaseResult" in repr(r)
        assert "1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = LowercaseResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = LowercaseResult(changes=[LowercaseChange("db_host", "DB_HOST", "val")])
        assert r.has_changes

    def test_changed_keys_returns_old_keys(self):
        r = LowercaseResult(changes=[LowercaseChange("db_host", "DB_HOST", "val")])
        assert "DB_HOST" in r.changed_keys


class TestEnvLowercaser:
    def test_already_lowercase_no_changes(self, lowercaser):
        vars = {"host": "localhost", "port": "5432"}
        result = lowercaser.lowercase(vars)
        assert not result.has_changes
        assert result.vars == vars

    def test_uppercase_keys_are_lowercased(self, lowercaser, sample_vars):
        result = lowercaser.lowercase(sample_vars)
        assert "db_host" in result.vars
        assert "api_key" in result.vars
        assert "port" in result.vars

    def test_values_preserved(self, lowercaser, sample_vars):
        result = lowercaser.lowercase(sample_vars)
        assert result.vars["db_host"] == "localhost"
        assert result.vars["api_key"] == "secret"

    def test_change_records_correct_keys(self, lowercaser, sample_vars):
        result = lowercaser.lowercase(sample_vars)
        old_keys = result.changed_keys
        assert "DB_HOST" in old_keys
        assert "API_KEY" in old_keys
        assert "port" not in old_keys

    def test_collision_without_overwrite_keeps_original(self, lowercaser):
        vars = {"DB_HOST": "upper", "db_host": "lower"}
        result = lowercaser.lowercase(vars)
        # existing lowercase key wins; uppercase key kept as-is
        assert "db_host" in result.vars
        assert "DB_HOST" in result.vars

    def test_collision_with_overwrite_replaces(self, overwrite_lowercaser):
        vars = {"db_host": "lower", "DB_HOST": "upper"}
        result = overwrite_lowercaser.lowercase(vars)
        assert result.vars["db_host"] == "upper"

    def test_mixed_case_keys(self, lowercaser):
        vars = {"MyKey": "val1", "ANOTHER_KEY": "val2"}
        result = lowercaser.lowercase(vars)
        assert "mykey" in result.vars
        assert "another_key" in result.vars
        assert result.has_changes
