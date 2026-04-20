"""Tests for EnvSpotlight."""
import pytest
from envoy.env_spotlight import EnvSpotlight, SpotlightMatch, SpotlightResult


@pytest.fixture
def spotlight():
    return EnvSpotlight(["SECRET", "TOKEN", "URL"])


@pytest.fixture
def sample_vars():
    return {
        "DB_URL": "postgres://localhost/db",
        "API_TOKEN": "abc123",
        "APP_SECRET": "s3cr3t",
        "DEBUG": "true",
        "PORT": "8080",
    }


class TestSpotlightResult:
    def test_repr(self):
        r = SpotlightResult()
        assert "SpotlightResult" in repr(r)
        assert "matches=0" in repr(r)

    def test_found_false_when_empty(self):
        assert SpotlightResult().found is False

    def test_found_true_when_matches(self):
        m = SpotlightMatch(key="API_TOKEN", value="x", pattern="TOKEN", priority=1)
        assert SpotlightResult(matches=[m]).found is True

    def test_top_priority_none_when_empty(self):
        assert SpotlightResult().top_priority is None

    def test_top_priority_lowest_number(self):
        m1 = SpotlightMatch("A", "1", "SECRET", priority=1)
        m2 = SpotlightMatch("B", "2", "TOKEN", priority=2)
        r = SpotlightResult(matches=[m2, m1])
        assert r.top_priority.priority == 1

    def test_matched_keys_list(self):
        m = SpotlightMatch("API_TOKEN", "x", "TOKEN", priority=2)
        r = SpotlightResult(matches=[m])
        assert "API_TOKEN" in r.matched_keys


class TestEnvSpotlight:
    def test_no_matches_returns_all_unmatched(self, sample_vars):
        s = EnvSpotlight(["NONEXISTENT"])
        result = s.scan(sample_vars)
        assert not result.found
        assert len(result.unmatched_keys) == len(sample_vars)

    def test_matches_by_pattern(self, spotlight, sample_vars):
        result = spotlight.scan(sample_vars)
        assert result.found
        matched = result.matched_keys
        assert "API_TOKEN" in matched
        assert "APP_SECRET" in matched
        assert "DB_URL" in matched

    def test_unmatched_keys_excluded_from_matches(self, spotlight, sample_vars):
        result = spotlight.scan(sample_vars)
        for k in result.unmatched_keys:
            assert k not in result.matched_keys

    def test_priority_assigned_by_pattern_order(self, spotlight, sample_vars):
        result = spotlight.scan(sample_vars)
        secret_match = next(m for m in result.matches if m.key == "APP_SECRET")
        token_match = next(m for m in result.matches if m.key == "API_TOKEN")
        assert secret_match.priority == 1   # "SECRET" is index 0 -> priority 1
        assert token_match.priority == 2    # "TOKEN" is index 1 -> priority 2

    def test_case_insensitive_by_default(self):
        s = EnvSpotlight(["secret"])
        result = s.scan({"APP_SECRET": "val"})
        assert result.found

    def test_case_sensitive_mode(self):
        s = EnvSpotlight(["secret"], case_sensitive=True)
        result = s.scan({"APP_SECRET": "val"})  # uppercase key won't match lowercase pattern
        assert not result.found

    def test_each_key_matched_by_first_pattern_only(self):
        # KEY matches both P1 and P2; should only appear once with P1
        s = EnvSpotlight(["KEY", "MY_KEY"])
        result = s.scan({"MY_KEY": "v"})
        assert len([m for m in result.matches if m.key == "MY_KEY"]) == 1
        assert result.matches[0].priority == 1

    def test_results_sorted_by_priority_then_key(self):
        s = EnvSpotlight(["URL", "TOKEN"])
        vars_ = {"Z_TOKEN": "a", "A_TOKEN": "b", "MY_URL": "c"}
        result = s.scan(vars_)
        assert result.matches[0].key == "MY_URL"   # priority 1
        assert result.matches[1].key == "A_TOKEN"  # priority 2, alphabetically first
        assert result.matches[2].key == "Z_TOKEN"  # priority 2, alphabetically second
