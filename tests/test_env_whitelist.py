import pytest
from envoy.env_whitelist import EnvWhitelist, WhitelistResult, WhitelistViolation


@pytest.fixture
def whitelist():
    return EnvWhitelist(allowed_keys=["APP_NAME", "APP_ENV", "PORT"])


@pytest.fixture
def sample_vars():
    return {"APP_NAME": "myapp", "APP_ENV": "production", "PORT": "8080"}


class TestWhitelistViolation:
    def test_repr_contains_key_and_reason(self):
        v = WhitelistViolation(key="SECRET", reason="key not in whitelist")
        assert "SECRET" in repr(v)
        assert "key not in whitelist" in repr(v)


class TestWhitelistResult:
    def test_repr(self):
        r = WhitelistResult(allowed={"A": "1"}, violations=[])
        assert "allowed=1" in repr(r)
        assert "violations=0" in repr(r)

    def test_is_clean_when_no_violations(self):
        r = WhitelistResult(allowed={"A": "1"}, violations=[])
        assert r.is_clean is True

    def test_not_clean_when_violations_present(self):
        v = WhitelistViolation(key="BAD", reason="key not in whitelist")
        r = WhitelistResult(allowed={}, violations=[v])
        assert r.is_clean is False


class TestEnvWhitelist:
    def test_all_allowed_keys_pass(self, whitelist, sample_vars):
        result = whitelist.check(sample_vars)
        assert result.is_clean
        assert result.allowed == sample_vars
        assert result.violations == []

    def test_unknown_key_produces_violation(self, whitelist):
        vars_ = {"APP_NAME": "x", "UNKNOWN_KEY": "y"}
        result = whitelist.check(vars_)
        assert not result.is_clean
        assert len(result.violations) == 1
        assert result.violations[0].key == "UNKNOWN_KEY"

    def test_filter_removes_unknown_keys(self, whitelist):
        vars_ = {"APP_NAME": "x", "UNKNOWN_KEY": "y", "PORT": "80"}
        filtered = whitelist.filter(vars_)
        assert "UNKNOWN_KEY" not in filtered
        assert "APP_NAME" in filtered
        assert "PORT" in filtered

    def test_filter_empty_vars(self, whitelist):
        assert whitelist.filter({}) == {}

    def test_allowed_keys_sorted(self):
        wl = EnvWhitelist(allowed_keys=["Z_KEY", "A_KEY", "M_KEY"])
        assert wl.allowed_keys == ["A_KEY", "M_KEY", "Z_KEY"]

    def test_empty_whitelist_blocks_everything(self):
        wl = EnvWhitelist(allowed_keys=[])
        result = wl.check({"SOME_VAR": "val"})
        assert not result.is_clean
        assert len(result.violations) == 1

    def test_multiple_violations_reported(self, whitelist):
        vars_ = {"EXTRA_ONE": "a", "EXTRA_TWO": "b"}
        result = whitelist.check(vars_)
        assert len(result.violations) == 2
        violation_keys = {v.key for v in result.violations}
        assert violation_keys == {"EXTRA_ONE", "EXTRA_TWO"}
