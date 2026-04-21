import pytest
from envoy.env_replace import EnvReplacer, ReplaceChange, ReplaceResult


@pytest.fixture
def replacer():
    return EnvReplacer(pattern="localhost", replacement="prod.example.com")


@pytest.fixture
def selective_replacer():
    return EnvReplacer(pattern="old", replacement="new", keys=["DB_HOST"])


@pytest.fixture
def sample_vars():
    return {
        "DB_HOST": "localhost",
        "REDIS_URL": "redis://localhost:6379",
        "APP_NAME": "myapp",
    }


class TestReplaceResult:
    def test_repr(self):
        r = ReplaceResult(changes=[ReplaceChange("A", "old", "new")], skipped=["B"])
        assert "1" in repr(r)
        assert "1" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert ReplaceResult().has_changes() is False

    def test_has_changes_true_when_populated(self):
        r = ReplaceResult(changes=[ReplaceChange("K", "a", "b")])
        assert r.has_changes() is True

    def test_changed_keys(self):
        r = ReplaceResult(changes=[ReplaceChange("X", "1", "2"), ReplaceChange("Y", "3", "4")])
        assert r.changed_keys() == ["X", "Y"]


class TestEnvReplacer:
    def test_replaces_matching_value(self, replacer, sample_vars):
        result = replacer.replace(sample_vars)
        assert result.has_changes()
        keys = result.changed_keys()
        assert "DB_HOST" in keys
        assert "REDIS_URL" in keys

    def test_no_match_no_changes(self, sample_vars):
        r = EnvReplacer(pattern="nonexistent", replacement="x")
        result = r.replace(sample_vars)
        assert not result.has_changes()

    def test_selective_keys_only_affects_listed(self, selective_replacer):
        vars_ = {"DB_HOST": "old_host", "API_URL": "old_api"}
        result = selective_replacer.replace(vars_)
        assert len(result.changes) == 1
        assert result.changes[0].key == "DB_HOST"
        assert "API_URL" in result.skipped

    def test_apply_returns_updated_dict(self, replacer, sample_vars):
        updated = replacer.apply(sample_vars)
        assert updated["DB_HOST"] == "prod.example.com"
        assert "prod.example.com" in updated["REDIS_URL"]
        assert updated["APP_NAME"] == "myapp"

    def test_original_dict_not_mutated(self, replacer, sample_vars):
        original_host = sample_vars["DB_HOST"]
        replacer.apply(sample_vars)
        assert sample_vars["DB_HOST"] == original_host

    def test_replace_change_repr(self):
        c = ReplaceChange(key="K", old_value="old", new_value="new")
        assert "K" in repr(c)
        assert "old" in repr(c)
        assert "new" in repr(c)

    def test_empty_replacement(self, sample_vars):
        r = EnvReplacer(pattern="localhost", replacement="")
        result = r.replace(sample_vars)
        updated = r.apply(sample_vars)
        assert updated["DB_HOST"] == ""
        assert result.has_changes()
