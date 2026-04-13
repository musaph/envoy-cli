"""Tests for EnvInheritor."""
import pytest
from envoy.env_inherit import EnvInheritor, InheritResult, InheritChange


@pytest.fixture
def inheritor() -> EnvInheritor:
    return EnvInheritor()


@pytest.fixture
def sample_base() -> dict:
    return {"APP_ENV": "production", "DB_HOST": "db.prod", "LOG_LEVEL": "warn"}


@pytest.fixture
def sample_child() -> dict:
    return {"APP_ENV": "staging", "EXTRA_KEY": "hello"}


class TestInheritResult:
    def test_repr(self):
        r = InheritResult(vars={"A": "1"}, changes=[])
        assert "InheritResult" in repr(r)

    def test_has_overrides_false_when_all_base(self, inheritor, sample_base):
        result = inheritor.inherit(sample_base, {})
        assert not result.has_overrides

    def test_has_overrides_true_when_child_wins(self, inheritor, sample_base, sample_child):
        result = inheritor.inherit(sample_base, sample_child)
        assert result.has_overrides

    def test_inherited_keys_lists_base_only_keys(self, inheritor, sample_base, sample_child):
        result = inheritor.inherit(sample_base, sample_child)
        assert "DB_HOST" in result.inherited_keys
        assert "LOG_LEVEL" in result.inherited_keys
        assert "APP_ENV" not in result.inherited_keys


class TestEnvInheritor:
    def test_child_overrides_base(self, inheritor, sample_base, sample_child):
        result = inheritor.inherit(sample_base, sample_child)
        assert result.vars["APP_ENV"] == "staging"

    def test_base_keys_present_in_result(self, inheritor, sample_base, sample_child):
        result = inheritor.inherit(sample_base, sample_child)
        assert result.vars["DB_HOST"] == "db.prod"
        assert result.vars["LOG_LEVEL"] == "warn"

    def test_child_only_keys_included(self, inheritor, sample_base, sample_child):
        result = inheritor.inherit(sample_base, sample_child)
        assert result.vars["EXTRA_KEY"] == "hello"

    def test_empty_base_returns_child(self, inheritor, sample_child):
        result = inheritor.inherit({}, sample_child)
        assert result.vars == sample_child

    def test_empty_child_returns_base(self, inheritor, sample_base):
        result = inheritor.inherit(sample_base, {})
        assert result.vars == sample_base

    def test_allow_empty_override_false_keeps_base_value(self):
        inheritor = EnvInheritor(allow_empty_override=False)
        base = {"KEY": "base_val"}
        child = {"KEY": ""}
        result = inheritor.inherit(base, child)
        assert result.vars["KEY"] == "base_val"

    def test_allow_empty_override_true_uses_empty_child(self):
        inheritor = EnvInheritor(allow_empty_override=True)
        base = {"KEY": "base_val"}
        child = {"KEY": ""}
        result = inheritor.inherit(base, child)
        assert result.vars["KEY"] == ""

    def test_change_source_correct(self, inheritor, sample_base, sample_child):
        result = inheritor.inherit(sample_base, sample_child)
        by_key = {c.key: c for c in result.changes}
        assert by_key["APP_ENV"].source == "child"
        assert by_key["DB_HOST"].source == "base"
        assert by_key["EXTRA_KEY"].source == "child"

    def test_change_repr(self):
        c = InheritChange("KEY", "base", "v1", None, "v1")
        assert "KEY" in repr(c)
        assert "base" in repr(c)
