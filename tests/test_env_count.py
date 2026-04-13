import pytest
from envoy.env_count import CountResult, EnvCounter


@pytest.fixture
def counter():
    return EnvCounter()


@pytest.fixture
def sample_vars():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_PASSWORD": "",
        "APP_NAME": "envoy",
        "APP_DEBUG": "",
        "SECRET_KEY": "abc123",
    }


class TestCountResult:
    def test_repr(self):
        r = CountResult(total=5, set_count=3, empty_count=2)
        assert "total=5" in repr(r)
        assert "set=3" in repr(r)
        assert "empty=2" in repr(r)

    def test_unset_ratio_zero_when_no_total(self):
        r = CountResult()
        assert r.unset_ratio == 0.0

    def test_unset_ratio_calculated(self):
        r = CountResult(total=4, set_count=3, empty_count=1)
        assert r.unset_ratio == pytest.approx(0.25)

    def test_defaults_are_zero(self):
        r = CountResult()
        assert r.total == 0
        assert r.set_count == 0
        assert r.empty_count == 0
        assert r.by_prefix == {}


class TestEnvCounter:
    def test_total_count(self, counter, sample_vars):
        result = counter.count(sample_vars)
        assert result.total == 6

    def test_set_count(self, counter, sample_vars):
        result = counter.count(sample_vars)
        assert result.set_count == 4

    def test_empty_count(self, counter, sample_vars):
        result = counter.count(sample_vars)
        assert result.empty_count == 2

    def test_by_prefix(self, counter, sample_vars):
        result = counter.count(sample_vars)
        assert result.by_prefix["DB"] == 3
        assert result.by_prefix["APP"] == 2
        assert result.by_prefix["SECRET"] == 1

    def test_empty_vars(self, counter):
        result = counter.count({})
        assert result.total == 0
        assert result.by_prefix == {}

    def test_no_prefix_vars_excluded_from_by_prefix(self, counter):
        result = counter.count({"NODASH": "value"})
        assert result.by_prefix == {}

    def test_whitespace_value_counts_as_empty(self, counter):
        result = counter.count({"KEY": "   "})
        assert result.empty_count == 1

    def test_custom_delimiter(self):
        c = EnvCounter(prefix_delimiters=["-"])
        result = c.count({"app-name": "x", "app-debug": "y", "plain": "z"})
        assert result.by_prefix.get("app") == 2
