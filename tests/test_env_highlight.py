import pytest
from envoy.env_highlight import EnvHighlighter, HighlightMatch, HighlightResult


@pytest.fixture
def highlighter():
    return EnvHighlighter(patterns=[r"secret", r"token"])


@pytest.fixture
def sample_vars():
    return {
        "API_TOKEN": "abc123",
        "DB_SECRET": "hunter2",
        "APP_NAME": "myapp",
        "PORT": "8080",
        "SECRET_KEY": "xyz789",
    }


class TestHighlightResult:
    def test_repr(self):
        r = HighlightResult(matches=[HighlightMatch("K", "v", "p")], unmatched_keys=["X"])
        assert "matches=1" in repr(r)
        assert "unmatched=1" in repr(r)

    def test_found_false_when_empty(self):
        r = HighlightResult()
        assert r.found is False

    def test_found_true_when_matches(self):
        r = HighlightResult(matches=[HighlightMatch("K", "v", "p")])
        assert r.found is True

    def test_matched_keys(self):
        r = HighlightResult(matches=[
            HighlightMatch("FOO", "bar", "p1"),
            HighlightMatch("BAZ", "qux", "p2"),
        ])
        assert r.matched_keys == ["FOO", "BAZ"]


class TestEnvHighlighter:
    def test_matches_key_by_pattern(self, highlighter, sample_vars):
        result = highlighter.highlight(sample_vars)
        assert result.found
        matched = result.matched_keys
        assert "API_TOKEN" in matched
        assert "DB_SECRET" in matched
        assert "SECRET_KEY" in matched

    def test_unmatched_keys_excluded(self, highlighter, sample_vars):
        result = highlighter.highlight(sample_vars)
        assert "APP_NAME" in result.unmatched_keys
        assert "PORT" in result.unmatched_keys

    def test_case_insensitive_by_default(self, sample_vars):
        h = EnvHighlighter(patterns=[r"api"])
        result = h.highlight(sample_vars)
        assert "API_TOKEN" in result.matched_keys

    def test_case_sensitive_no_match(self, sample_vars):
        h = EnvHighlighter(patterns=[r"api"], case_sensitive=True)
        result = h.highlight(sample_vars)
        assert "API_TOKEN" not in result.matched_keys

    def test_highlight_keys_only_ignores_value(self):
        h = EnvHighlighter(patterns=[r"secret"])
        vars = {"NORMAL_KEY": "my_secret_value", "SECRET_KEY": "plain"}
        result = h.highlight_keys_only(vars)
        assert "SECRET_KEY" in result.matched_keys
        assert "NORMAL_KEY" not in result.matched_keys

    def test_highlight_matches_value_too(self):
        h = EnvHighlighter(patterns=[r"secret"])
        vars = {"NORMAL_KEY": "my_secret_value"}
        result = h.highlight(vars)
        assert "NORMAL_KEY" in result.matched_keys

    def test_no_patterns_match_nothing(self, sample_vars):
        h = EnvHighlighter(patterns=[])
        result = h.highlight(sample_vars)
        assert not result.found
        assert len(result.unmatched_keys) == len(sample_vars)

    def test_match_records_correct_pattern(self, sample_vars):
        result = highlighter().highlight(sample_vars) if False else EnvHighlighter([r"token"]).highlight(sample_vars)
        token_match = next((m for m in result.matches if m.key == "API_TOKEN"), None)
        assert token_match is not None
        assert token_match.pattern == r"token"
