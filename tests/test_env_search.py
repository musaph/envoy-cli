import pytest
from envoy.env_search import EnvSearch, SearchMatch, SearchResult


@pytest.fixture
def searcher():
    return EnvSearch()


@pytest.fixture
def sample_vars():
    return {
        "DATABASE_URL": "postgres://localhost/mydb",
        "API_KEY": "secret123",
        "APP_ENV": "production",
        "DEBUG": "false",
        "AWS_SECRET_ACCESS_KEY": "abc",
    }


class TestSearchResult:
    def test_repr(self):
        r = SearchResult(query="foo", matches=[])
        assert "foo" in repr(r)
        assert "0" in repr(r)

    def test_found_false_when_empty(self):
        r = SearchResult(query="x")
        assert not r.found

    def test_found_true_with_matches(self):
        m = SearchMatch(key="K", value="v", match_on="key")
        r = SearchResult(matches=[m], query="K")
        assert r.found

    def test_keys_property(self):
        m1 = SearchMatch(key="A", value="1", match_on="key")
        m2 = SearchMatch(key="B", value="2", match_on="value")
        r = SearchResult(matches=[m1, m2], query="")
        assert r.keys == ["A", "B"]


class TestEnvSearch:
    def test_search_by_key_substring(self, searcher, sample_vars):
        result = searcher.search(sample_vars, "API")
        assert result.found
        assert "API_KEY" in result.keys

    def test_search_by_value_substring(self, searcher, sample_vars):
        result = searcher.search(sample_vars, "postgres")
        assert result.found
        assert "DATABASE_URL" in result.keys
        assert result.matches[0].match_on == "value"

    def test_search_case_insensitive_default(self, searcher, sample_vars):
        result = searcher.search(sample_vars, "debug")
        assert result.found
        assert "DEBUG" in result.keys

    def test_search_case_sensitive_misses(self, sample_vars):
        s = EnvSearch(case_sensitive=True)
        result = s.search(sample_vars, "debug")
        assert not result.found

    def test_search_keys_only_skips_values(self, sample_vars):
        s = EnvSearch(search_values=False)
        result = s.search(sample_vars, "postgres")
        assert not result.found

    def test_search_match_on_both(self, sample_vars):
        # 'KEY' appears in key name and value substring scenario
        vars_ = {"MY_KEY": "some_key_value"}
        result = searcher_inst = EnvSearch()
        r = searcher_inst.search(vars_, "key")
        assert r.matches[0].match_on == "both"

    def test_search_regex_pattern(self, searcher, sample_vars):
        result = searcher.search(sample_vars, r"^APP_")
        assert "APP_ENV" in result.keys
        assert "API_KEY" not in result.keys

    def test_search_invalid_regex_falls_back_to_literal(self, searcher, sample_vars):
        result = searcher.search(sample_vars, "[invalid")
        # Should not raise, just no matches for literal "[invalid"
        assert isinstance(result, SearchResult)

    def test_filter_by_prefix(self, searcher, sample_vars):
        filtered = searcher.filter_by_prefix(sample_vars, "AWS")
        assert "AWS_SECRET_ACCESS_KEY" in filtered
        assert len(filtered) == 1

    def test_filter_by_prefix_case_insensitive(self, sample_vars):
        s = EnvSearch(case_sensitive=False)
        filtered = s.filter_by_prefix(sample_vars, "aws")
        assert "AWS_SECRET_ACCESS_KEY" in filtered

    def test_filter_by_prefix_no_match(self, searcher, sample_vars):
        filtered = searcher.filter_by_prefix(sample_vars, "NONEXISTENT")
        assert filtered == {}
