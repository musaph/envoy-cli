import pytest
from envoy.env_prefix import EnvPrefixer, PrefixChange, PrefixResult


@pytest.fixture
def prefixer():
    return EnvPrefixer(prefix="APP")


@pytest.fixture
def sample_vars():
    return {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "abc123",
        "DEBUG": "true",
    }


class TestPrefixResult:
    def test_repr(self):
        r = PrefixResult(original={}, renamed={}, changes=[], skipped=[])
        assert "PrefixResult" in repr(r)
        assert "changes=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = PrefixResult(original={}, renamed={}, changes=[], skipped=[])
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        change = PrefixChange(key="FOO", new_key="APP_FOO", value="bar")
        r = PrefixResult(original={}, renamed={}, changes=[change], skipped=[])
        assert r.has_changes


class TestPrefixChangeRepr:
    def test_repr_contains_keys(self):
        c = PrefixChange(key="FOO", new_key="APP_FOO", value="bar")
        assert "FOO" in repr(c)
        assert "APP_FOO" in repr(c)


class TestEnvPrefixer:
    def test_empty_prefix_raises(self):
        with pytest.raises(ValueError):
            EnvPrefixer(prefix="")

    def test_prefix_is_uppercased(self):
        p = EnvPrefixer(prefix="app")
        assert p.prefix == "APP"

    def test_add_prefix_renames_keys(self, prefixer, sample_vars):
        result = prefixer.add(sample_vars)
        assert "APP_DATABASE_URL" in result.renamed
        assert "APP_SECRET_KEY" in result.renamed
        assert "APP_DEBUG" in result.renamed

    def test_add_prefix_preserves_values(self, prefixer, sample_vars):
        result = prefixer.add(sample_vars)
        assert result.renamed["APP_DATABASE_URL"] == "postgres://localhost/db"

    def test_add_prefix_skips_already_prefixed(self, prefixer):
        vars_ = {"APP_FOO": "bar", "BAZ": "qux"}
        result = prefixer.add(vars_)
        assert "APP_FOO" in result.skipped
        assert "APP_BAZ" in result.renamed
        assert len(result.changes) == 1

    def test_add_prefix_change_count(self, prefixer, sample_vars):
        result = prefixer.add(sample_vars)
        assert len(result.changes) == 3

    def test_remove_prefix_strips_prefix(self, prefixer):
        vars_ = {"APP_FOO": "1", "APP_BAR": "2"}
        result = prefixer.remove(vars_)
        assert "FOO" in result.renamed
        assert "BAR" in result.renamed

    def test_remove_prefix_skips_unprefixed(self, prefixer):
        vars_ = {"APP_FOO": "1", "OTHER": "2"}
        result = prefixer.remove(vars_)
        assert "OTHER" in result.skipped
        assert "OTHER" in result.renamed

    def test_remove_preserves_values(self, prefixer):
        vars_ = {"APP_KEY": "secret"}
        result = prefixer.remove(vars_)
        assert result.renamed["KEY"] == "secret"

    def test_filter_returns_only_prefixed(self, prefixer):
        vars_ = {"APP_FOO": "1", "BAR": "2", "APP_BAZ": "3"}
        filtered = prefixer.filter(vars_)
        assert set(filtered.keys()) == {"APP_FOO", "APP_BAZ"}

    def test_filter_empty_when_no_match(self, prefixer):
        vars_ = {"FOO": "1", "BAR": "2"}
        filtered = prefixer.filter(vars_)
        assert filtered == {}

    def test_custom_separator(self):
        p = EnvPrefixer(prefix="NS", separator=".")
        result = p.add({"KEY": "val"})
        assert "NS.KEY" in result.renamed

    def test_original_not_mutated(self, prefixer, sample_vars):
        original_keys = set(sample_vars.keys())
        prefixer.add(sample_vars)
        assert set(sample_vars.keys()) == original_keys
