import pytest
from envoy.env_trim_keys import EnvKeyTrimmer, TrimKeyChange, TrimKeyResult


@pytest.fixture
def trimmer():
    return EnvKeyTrimmer()


@pytest.fixture
def overwrite_trimmer():
    return EnvKeyTrimmer(overwrite=True)


@pytest.fixture
def custom_trimmer():
    return EnvKeyTrimmer(chars="_")


@pytest.fixture
def sample_vars():
    return {
        "  DB_HOST  ": "localhost",
        "DB_PORT": "5432",
        "  API_KEY": "secret",
        "CLEAN_KEY": "value",
    }


class TestTrimKeyResult:
    def test_repr(self):
        r = TrimKeyResult(changes=[TrimKeyChange("  A", "A")], skipped=["B"])
        assert "TrimKeyResult" in repr(r)
        assert "changes=1" in repr(r)
        assert "skipped=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = TrimKeyResult()
        assert not r.has_changes()

    def test_has_changes_true_when_populated(self):
        r = TrimKeyResult(changes=[TrimKeyChange("  X", "X")])
        assert r.has_changes()

    def test_changed_keys_returns_originals(self):
        r = TrimKeyResult(changes=[TrimKeyChange("  A", "A"), TrimKeyChange("B  ", "B")])
        assert r.changed_keys() == ["  A", "B  "]


class TestTrimKeyChange:
    def test_repr_contains_keys(self):
        c = TrimKeyChange(original="  FOO", trimmed="FOO")
        assert "  FOO" in repr(c)
        assert "FOO" in repr(c)


class TestEnvKeyTrimmer:
    def test_clean_keys_unchanged(self, trimmer):
        vars = {"DB_HOST": "localhost", "PORT": "5432"}
        result = trimmer.trim(vars)
        assert not result.has_changes()
        assert result.vars == vars

    def test_leading_whitespace_trimmed(self, trimmer):
        vars = {"  DB_HOST": "localhost"}
        result = trimmer.trim(vars)
        assert result.has_changes()
        assert "DB_HOST" in result.vars
        assert "  DB_HOST" not in result.vars

    def test_trailing_whitespace_trimmed(self, trimmer):
        vars = {"API_KEY  ": "secret"}
        result = trimmer.trim(vars)
        assert result.has_changes()
        assert "API_KEY" in result.vars

    def test_both_sides_trimmed(self, trimmer, sample_vars):
        result = trimmer.trim(sample_vars)
        assert "DB_HOST" in result.vars
        assert "API_KEY" in result.vars
        assert "DB_PORT" in result.vars

    def test_empty_key_after_trim_is_skipped(self, trimmer):
        vars = {"   ": "value"}
        result = trimmer.trim(vars)
        assert not result.has_changes()
        assert "   " in result.skipped

    def test_conflict_skipped_without_overwrite(self, trimmer):
        vars = {"  DB_HOST": "remote", "DB_HOST": "local"}
        result = trimmer.trim(vars)
        assert "  DB_HOST" in result.skipped
        assert result.vars["DB_HOST"] == "local"

    def test_conflict_resolved_with_overwrite(self, overwrite_trimmer):
        vars = {"  DB_HOST": "remote", "DB_HOST": "local"}
        result = overwrite_trimmer.trim(vars)
        assert "DB_HOST" in result.vars
        assert result.vars["DB_HOST"] == "remote"

    def test_custom_chars_trimmed(self, custom_trimmer):
        vars = {"__SECRET__": "value", "NORMAL": "ok"}
        result = custom_trimmer.trim(vars)
        assert "SECRET" in result.vars
        assert "NORMAL" in result.vars
        assert result.has_changes()

    def test_value_preserved_after_trim(self, trimmer):
        vars = {"  MY_VAR  ": "hello world"}
        result = trimmer.trim(vars)
        assert result.vars.get("MY_VAR") == "hello world"
