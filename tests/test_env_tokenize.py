"""Tests for EnvTokenizer."""
from __future__ import annotations

import pytest
from envoy.env_tokenize import EnvTokenizer, TokenizeChange, TokenizeResult


@pytest.fixture
def tokenizer() -> EnvTokenizer:
    return EnvTokenizer()


@pytest.fixture
def sample_vars() -> dict:
    return {
        "ALLOWED_HOSTS": "localhost,127.0.0.1,example.com",
        "TAGS": "web api backend",
        "SINGLE": "onlyone",
        "PIPE_LIST": "alpha|beta|gamma",
        "EMPTY": "",
    }


class TestTokenizeResult:
    def test_repr(self):
        r = TokenizeResult(changes=[TokenizeChange("K", "a,b", ["a", "b"])], skipped=["X"])
        assert "changes=1" in repr(r)
        assert "skipped=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = TokenizeResult()
        assert r.has_changes() is False

    def test_has_changes_true_when_populated(self):
        r = TokenizeResult(changes=[TokenizeChange("K", "a,b", ["a", "b"])])
        assert r.has_changes() is True

    def test_changed_keys(self):
        r = TokenizeResult(
            changes=[
                TokenizeChange("A", "x,y", ["x", "y"]),
                TokenizeChange("B", "p q", ["p", "q"]),
            ]
        )
        assert r.changed_keys() == ["A", "B"]


class TestEnvTokenizer:
    def test_comma_separated(self, tokenizer, sample_vars):
        result = tokenizer.tokenize({"ALLOWED_HOSTS": sample_vars["ALLOWED_HOSTS"]})
        assert result.has_changes()
        assert result.changes[0].tokens == ["localhost", "127.0.0.1", "example.com"]

    def test_space_separated(self, tokenizer, sample_vars):
        result = tokenizer.tokenize({"TAGS": sample_vars["TAGS"]})
        assert result.changes[0].tokens == ["web", "api", "backend"]

    def test_pipe_separated(self, tokenizer, sample_vars):
        result = tokenizer.tokenize({"PIPE_LIST": sample_vars["PIPE_LIST"]})
        assert result.changes[0].tokens == ["alpha", "beta", "gamma"]

    def test_single_token_is_skipped(self, tokenizer, sample_vars):
        result = tokenizer.tokenize({"SINGLE": sample_vars["SINGLE"]})
        assert not result.has_changes()
        assert "SINGLE" in result.skipped

    def test_empty_value_is_skipped(self, tokenizer, sample_vars):
        result = tokenizer.tokenize({"EMPTY": sample_vars["EMPTY"]})
        assert "EMPTY" in result.skipped

    def test_restrict_to_keys(self, sample_vars):
        t = EnvTokenizer(keys=["TAGS"])
        result = t.tokenize(sample_vars)
        assert result.changed_keys() == ["TAGS"]

    def test_custom_pattern(self):
        t = EnvTokenizer(pattern=r"\|")
        result = t.tokenize({"V": "a|b|c"})
        assert result.changes[0].tokens == ["a", "b", "c"]

    def test_min_tokens_filter(self):
        t = EnvTokenizer(min_tokens=3)
        result = t.tokenize({"FEW": "a,b", "MANY": "a,b,c"})
        assert result.changed_keys() == ["MANY"]
        assert "FEW" in result.skipped

    def test_as_dict(self, tokenizer):
        result = tokenizer.tokenize({"K": "x,y,z"})
        d = tokenizer.as_dict(result)
        assert d == {"K": ["x", "y", "z"]}

    def test_token_change_repr(self):
        c = TokenizeChange("MY_KEY", "a,b", ["a", "b"])
        assert "MY_KEY" in repr(c)
        assert "['a', 'b']" in repr(c)
