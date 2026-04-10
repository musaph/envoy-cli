"""Tests for EnvCaster type casting utilities."""
import pytest
from envoy.env_cast import CastResult, EnvCaster


@pytest.fixture
def caster():
    return EnvCaster()


class TestCastResult:
    def test_repr_success(self):
        r = CastResult("PORT", "8080", 8080, "int", True)
        assert "PORT" in repr(r)
        assert "ok" in repr(r)

    def test_repr_failure(self):
        r = CastResult("X", "bad", "bad", "int", False, error="invalid literal")
        assert "error" in repr(r)


class TestEnvCasterInference:
    def test_infers_int(self, caster):
        r = caster.cast_value("PORT", "8080")
        assert r.casted == 8080
        assert r.cast_type == "int"
        assert r.success is True

    def test_infers_float(self, caster):
        r = caster.cast_value("RATIO", "3.14")
        assert r.casted == pytest.approx(3.14)
        assert r.cast_type == "float"

    def test_infers_bool_true(self, caster):
        for val in ["true", "True", "1", "yes", "on"]:
            r = caster.cast_value("FLAG", val)
            assert r.casted is True, f"Expected True for {val!r}"
            assert r.cast_type == "bool"

    def test_infers_bool_false(self, caster):
        for val in ["false", "False", "0", "no", "off"]:
            r = caster.cast_value("FLAG", val)
            assert r.casted is False, f"Expected False for {val!r}"

    def test_infers_string_fallback(self, caster):
        r = caster.cast_value("NAME", "production")
        assert r.casted == "production"
        assert r.cast_type == "str"


class TestEnvCasterWithHints:
    def test_hint_int(self, caster):
        r = caster.cast_value("WORKERS", "4", hint="int")
        assert r.casted == 4

    def test_hint_float(self, caster):
        r = caster.cast_value("TIMEOUT", "1.5", hint="float")
        assert r.casted == pytest.approx(1.5)

    def test_hint_bool(self, caster):
        r = caster.cast_value("DEBUG", "yes", hint="bool")
        assert r.casted is True

    def test_hint_list(self, caster):
        r = caster.cast_value("HOSTS", "a.com, b.com, c.com", hint="list")
        assert r.casted == ["a.com", "b.com", "c.com"]

    def test_hint_str_keeps_value(self, caster):
        r = caster.cast_value("NUM", "42", hint="str")
        assert r.casted == "42"
        assert r.cast_type == "str"

    def test_invalid_hint_falls_back_to_str(self, caster):
        r = caster.cast_value("X", "val", hint="unknown_type")
        assert r.casted == "val"

    def test_hint_int_bad_value_returns_raw(self, caster):
        r = caster.cast_value("PORT", "not_a_number", hint="int")
        assert r.success is False
        assert r.casted == "not_a_number"
        assert r.error is not None


class TestCastAll:
    def test_cast_all_mixed(self, caster):
        vars_dict = {"PORT": "9000", "DEBUG": "true", "APP": "myapp"}
        results = caster.cast_all(vars_dict)
        by_key = {r.key: r for r in results}
        assert by_key["PORT"].casted == 9000
        assert by_key["DEBUG"].casted is True
        assert by_key["APP"].casted == "myapp"

    def test_to_python_dict(self, caster):
        vars_dict = {"RETRIES": "3", "ENABLED": "false"}
        result = caster.to_python_dict(vars_dict)
        assert result == {"RETRIES": 3, "ENABLED": False}

    def test_cast_all_with_hints(self, caster):
        vars_dict = {"TAGS": "a,b,c", "COUNT": "5"}
        hints = {"TAGS": "list", "COUNT": "int"}
        result = caster.to_python_dict(vars_dict, hints=hints)
        assert result["TAGS"] == ["a", "b", "c"]
        assert result["COUNT"] == 5
