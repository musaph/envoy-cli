"""Tests for EnvCloaker."""
import pytest
from envoy.env_cloak import CloakChange, CloakResult, EnvCloaker, _CLOAK_SYMBOL


@pytest.fixture
def cloaker():
    return EnvCloaker(patterns=[r"secret", r"password", r"token"])


@pytest.fixture
def sample_vars():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "API_TOKEN": "abc123",
        "DEBUG": "true",
    }


class TestCloakResult:
    def test_repr(self):
        r = CloakResult(vars={"A": "1"}, changes=[CloakChange("A", "1", "<cloaked>")])
        assert "cloaked=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = CloakResult(vars={"A": "1"}, changes=[])
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = CloakResult(vars={}, changes=[CloakChange("X", "v", "<cloaked>")])
        assert r.has_changes

    def test_cloaked_keys_returns_list(self):
        r = CloakResult(
            vars={},
            changes=[CloakChange("A", "1", "<cloaked>"), CloakChange("B", "2", "<cloaked>")],
        )
        assert r.cloaked_keys == ["A", "B"]


class TestEnvCloaker:
    def test_cloak_matching_keys(self, cloaker, sample_vars):
        result = cloaker.cloak(sample_vars)
        assert result.vars["DB_PASSWORD"] == _CLOAK_SYMBOL
        assert result.vars["API_TOKEN"] == _CLOAK_SYMBOL

    def test_non_matching_keys_unchanged(self, cloaker, sample_vars):
        result = cloaker.cloak(sample_vars)
        assert result.vars["APP_NAME"] == "myapp"
        assert result.vars["DEBUG"] == "true"

    def test_change_count_correct(self, cloaker, sample_vars):
        result = cloaker.cloak(sample_vars)
        assert len(result.changes) == 2

    def test_case_insensitive_matching(self):
        c = EnvCloaker(patterns=[r"secret"])
        result = c.cloak({"MY_SECRET_KEY": "val", "SECRET": "x", "safe": "ok"})
        assert result.vars["MY_SECRET_KEY"] == _CLOAK_SYMBOL
        assert result.vars["SECRET"] == _CLOAK_SYMBOL
        assert result.vars["safe"] == "ok"

    def test_custom_symbol(self):
        c = EnvCloaker(patterns=[r"pwd"], symbol="***")
        result = c.cloak({"DB_PWD": "pass"})
        assert result.vars["DB_PWD"] == "***"

    def test_no_patterns_cloaks_nothing(self, sample_vars):
        c = EnvCloaker(patterns=[])
        result = c.cloak(sample_vars)
        assert not result.has_changes
        assert result.vars == sample_vars

    def test_uncloak_restores_values(self, cloaker, sample_vars):
        result = cloaker.cloak(sample_vars)
        restored = cloaker.uncloak(result.vars, sample_vars)
        assert restored["DB_PASSWORD"] == "s3cr3t"
        assert restored["API_TOKEN"] == "abc123"
        assert restored["APP_NAME"] == "myapp"

    def test_uncloak_ignores_missing_originals(self, cloaker):
        cloaked = {"DB_PASSWORD": _CLOAK_SYMBOL}
        restored = cloaker.uncloak(cloaked, {})
        assert restored["DB_PASSWORD"] == _CLOAK_SYMBOL
