import pytest
from envoy.env_typecheck import EnvTypeChecker, TypeViolation, TypeCheckResult


@pytest.fixture
def schema():
    return {
        "PORT": "int",
        "DEBUG": "bool",
        "API_URL": "url",
        "RATIO": "float",
        "NAME": "nonempty",
    }


@pytest.fixture
def checker(schema):
    return EnvTypeChecker(schema)


class TestTypeCheckResult:
    def test_repr(self):
        r = TypeCheckResult(checked=5, violations=[])
        assert "checked=5" in repr(r)
        assert "violations=0" in repr(r)

    def test_is_clean_when_no_violations(self):
        r = TypeCheckResult(violations=[], checked=3)
        assert r.is_clean is True

    def test_is_not_clean_with_violations(self):
        v = TypeViolation(key="PORT", expected_type="int", actual_value="abc", reason="not int")
        r = TypeCheckResult(violations=[v], checked=1)
        assert r.is_clean is False


class TestTypeViolation:
    def test_repr_contains_key_and_type(self):
        v = TypeViolation(key="PORT", expected_type="int", actual_value="abc", reason="bad")
        assert "PORT" in repr(v)
        assert "int" in repr(v)


class TestEnvTypeChecker:
    def test_valid_int_passes(self, checker):
        result = checker.check({"PORT": "8080"})
        assert result.is_clean
        assert result.checked == 1

    def test_invalid_int_fails(self, checker):
        result = checker.check({"PORT": "not_a_number"})
        assert not result.is_clean
        assert result.violations[0].key == "PORT"

    def test_valid_bool_passes(self, checker):
        for val in ("true", "false", "1", "0", "yes", "no"):
            result = checker.check({"DEBUG": val})
            assert result.is_clean, f"Expected {val!r} to be valid bool"

    def test_invalid_bool_fails(self, checker):
        result = checker.check({"DEBUG": "maybe"})
        assert not result.is_clean

    def test_valid_url_passes(self, checker):
        result = checker.check({"API_URL": "https://example.com"})
        assert result.is_clean

    def test_invalid_url_fails(self, checker):
        result = checker.check({"API_URL": "ftp://example.com"})
        assert not result.is_clean

    def test_valid_float_passes(self, checker):
        result = checker.check({"RATIO": "3.14"})
        assert result.is_clean

    def test_invalid_float_fails(self, checker):
        result = checker.check({"RATIO": "pi"})
        assert not result.is_clean

    def test_nonempty_passes(self, checker):
        result = checker.check({"NAME": "alice"})
        assert result.is_clean

    def test_nonempty_fails_on_blank(self, checker):
        result = checker.check({"NAME": "   "})
        assert not result.is_clean

    def test_missing_key_not_checked(self, checker):
        result = checker.check({})
        assert result.checked == 0
        assert result.is_clean

    def test_unknown_type_skipped(self):
        c = EnvTypeChecker({"FOO": "uuid"})
        result = c.check({"FOO": "anything"})
        assert result.is_clean

    def test_negative_int_valid(self, checker):
        result = checker.check({"PORT": "-1"})
        assert result.is_clean
