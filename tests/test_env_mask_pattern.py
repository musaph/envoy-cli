"""Tests for EnvMaskPattern."""
import re
import pytest
from envoy.env_mask_pattern import EnvMaskPattern, MaskPatternChange, MaskPatternResult


@pytest.fixture
def masker():
    return EnvMaskPattern()


@pytest.fixture
def reveal_masker():
    return EnvMaskPattern(reveal_chars=3)


class TestMaskPatternResult:
    def test_repr(self):
        r = MaskPatternResult(changes=[], output={})
        assert "MaskPatternResult" in repr(r)
        assert "has_changes=False" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = MaskPatternResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        c = MaskPatternChange(key="SECRET", original="abc", masked="********")
        r = MaskPatternResult(changes=[c], output={"SECRET": "********"})
        assert r.has_changes

    def test_changed_keys(self):
        c = MaskPatternChange(key="API_KEY", original="xyz", masked="********")
        r = MaskPatternResult(changes=[c], output={})
        assert "API_KEY" in r.changed_keys


class TestMaskPatternChangeRepr:
    def test_repr_contains_key(self):
        c = MaskPatternChange(key="TOKEN", original="secret", masked="********")
        assert "TOKEN" in repr(c)
        assert "masked" in repr(c)


class TestEnvMaskPattern:
    def test_non_sensitive_key_not_masked(self, masker):
        result = masker.apply({"APP_NAME": "myapp", "PORT": "8080"})
        assert result.output["APP_NAME"] == "myapp"
        assert result.output["PORT"] == "8080"
        assert not result.has_changes

    def test_password_key_is_masked(self, masker):
        result = masker.apply({"DB_PASSWORD": "s3cr3t"})
        assert result.output["DB_PASSWORD"] == "*" * 8
        assert result.has_changes

    def test_token_key_is_masked(self, masker):
        result = masker.apply({"AUTH_TOKEN": "abc123"})
        assert result.output["AUTH_TOKEN"] == "*" * 8

    def test_secret_key_is_masked(self, masker):
        result = masker.apply({"MY_SECRET": "topsecret"})
        assert result.output["MY_SECRET"] == "*" * 8

    def test_empty_value_not_changed(self, masker):
        result = masker.apply({"DB_PASSWORD": ""})
        assert result.output["DB_PASSWORD"] == ""
        assert not result.has_changes

    def test_reveal_chars_keeps_prefix(self, reveal_masker):
        result = reveal_masker.apply({"API_KEY": "abcXYZ"})
        assert result.output["API_KEY"].startswith("abc")
        assert "*" in result.output["API_KEY"]

    def test_reveal_chars_short_value_fully_masked(self, reveal_masker):
        result = reveal_masker.apply({"API_KEY": "ab"})
        assert result.output["API_KEY"] == "*" * 8

    def test_custom_key_pattern(self):
        masker = EnvMaskPattern(key_patterns=[re.compile(r"CUSTOM", re.IGNORECASE)])
        result = masker.apply({"CUSTOM_VAR": "value", "DB_PASSWORD": "pass"})
        assert result.output["CUSTOM_VAR"] == "*" * 8
        assert result.output["DB_PASSWORD"] == "pass"

    def test_value_pattern_masks_matching_values(self):
        masker = EnvMaskPattern(
            key_patterns=[],
            value_pattern=re.compile(r"^\d{4}-\d{4}$"),
        )
        result = masker.apply({"CARD": "1234-5678", "NAME": "alice"})
        assert result.output["CARD"] == "*" * 8
        assert result.output["NAME"] == "alice"

    def test_multiple_vars_mixed(self, masker):
        vars_ = {"HOST": "localhost", "SECRET_KEY": "hunter2", "PORT": "5432"}
        result = masker.apply(vars_)
        assert result.output["HOST"] == "localhost"
        assert result.output["SECRET_KEY"] == "*" * 8
        assert result.output["PORT"] == "5432"
        assert len(result.changes) == 1
