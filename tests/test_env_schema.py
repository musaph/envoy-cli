"""Tests for envoy.env_schema."""
import pytest
from envoy.env_schema import EnvSchema, SchemaField, SchemaResult


@pytest.fixture()
def simple_schema() -> EnvSchema:
    return EnvSchema(
        [
            SchemaField(key="APP_ENV", required=True, allowed_values=["dev", "prod", "test"]),
            SchemaField(key="PORT", required=True, pattern=r"\d+"),
            SchemaField(key="DEBUG", required=False),
        ]
    )


class TestSchemaResult:
    def test_is_valid_with_no_errors(self):
        r = SchemaResult()
        assert r.is_valid is True

    def test_is_invalid_with_errors(self):
        r = SchemaResult(errors=["something wrong"])
        assert r.is_valid is False

    def test_warnings_do_not_affect_validity(self):
        r = SchemaResult(warnings=["extra key found"])
        assert r.is_valid is True


class TestSchemaField:
    def test_missing_required_key(self):
        f = SchemaField(key="SECRET", required=True)
        errors = f.validate(None)
        assert any("required" in e for e in errors)

    def test_missing_optional_key_no_error(self):
        f = SchemaField(key="OPTIONAL", required=False)
        assert f.validate(None) == []

    def test_pattern_match_passes(self):
        f = SchemaField(key="PORT", pattern=r"\d+")
        assert f.validate("8080") == []

    def test_pattern_mismatch_fails(self):
        f = SchemaField(key="PORT", pattern=r"\d+")
        errors = f.validate("abc")
        assert errors
        assert "pattern" in errors[0]

    def test_allowed_values_pass(self):
        f = SchemaField(key="ENV", allowed_values=["dev", "prod"])
        assert f.validate("dev") == []

    def test_disallowed_value_fails(self):
        f = SchemaField(key="ENV", allowed_values=["dev", "prod"])
        errors = f.validate("staging")
        assert errors
        assert "allowed" in errors[0]


class TestEnvSchema:
    def test_valid_vars_pass(self, simple_schema):
        result = simple_schema.validate({"APP_ENV": "dev", "PORT": "3000"})
        assert result.is_valid
        assert result.errors == []

    def test_missing_required_key_fails(self, simple_schema):
        result = simple_schema.validate({"PORT": "3000"})
        assert not result.is_valid
        assert any("APP_ENV" in e for e in result.errors)

    def test_invalid_pattern_fails(self, simple_schema):
        result = simple_schema.validate({"APP_ENV": "dev", "PORT": "not-a-port"})
        assert not result.is_valid
        assert any("PORT" in e for e in result.errors)

    def test_extra_keys_produce_warnings(self, simple_schema):
        result = simple_schema.validate({"APP_ENV": "prod", "PORT": "80", "UNKNOWN": "x"})
        assert result.is_valid
        assert any("UNKNOWN" in w for w in result.warnings)

    def test_from_dict_builds_schema(self):
        raw = {
            "DATABASE_URL": {"required": True, "description": "Postgres DSN"},
            "LOG_LEVEL": {"required": False, "allowed_values": ["DEBUG", "INFO", "ERROR"]},
        }
        schema = EnvSchema.from_dict(raw)
        result = schema.validate({"DATABASE_URL": "postgres://localhost/db", "LOG_LEVEL": "INFO"})
        assert result.is_valid

    def test_from_dict_missing_required(self):
        raw = {"API_KEY": {"required": True}}
        schema = EnvSchema.from_dict(raw)
        result = schema.validate({})
        assert not result.is_valid
