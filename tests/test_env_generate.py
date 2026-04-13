"""Tests for EnvGenerator."""
import pytest
from envoy.env_generate import EnvGenerator, GenerateField, GenerateResult


@pytest.fixture
def generator():
    return EnvGenerator(length=24)


class TestGenerateResult:
    def test_repr(self):
        r = GenerateResult(generated={"A": "1"}, skipped=["B"], errors=[])
        assert "generated=1" in repr(r)
        assert "skipped=1" in repr(r)

    def test_has_errors_false_when_empty(self):
        r = GenerateResult()
        assert not r.has_errors

    def test_has_errors_true_when_populated(self):
        r = GenerateResult(errors=["missing KEY"])
        assert r.has_errors


class TestEnvGenerator:
    def test_default_value_used(self, generator):
        fields = [GenerateField(key="APP_ENV", default="production")]
        result = generator.generate(fields)
        assert result.generated["APP_ENV"] == "production"
        assert not result.has_errors

    def test_auto_secret_generates_string(self, generator):
        fields = [GenerateField(key="SECRET_KEY", auto="secret")]
        result = generator.generate(fields)
        assert "SECRET_KEY" in result.generated
        assert len(result.generated["SECRET_KEY"]) == 24

    def test_auto_token_generates_string(self, generator):
        fields = [GenerateField(key="API_TOKEN", auto="token")]
        result = generator.generate(fields)
        assert len(result.generated["API_TOKEN"]) == 24

    def test_auto_uuid_generates_uuid(self, generator):
        fields = [GenerateField(key="APP_ID", auto="uuid")]
        result = generator.generate(fields)
        val = result.generated["APP_ID"]
        assert len(val) == 36
        assert val.count("-") == 4

    def test_required_field_without_value_is_error(self, generator):
        fields = [GenerateField(key="DB_PASSWORD", required=True)]
        result = generator.generate(fields)
        assert result.has_errors
        assert "DB_PASSWORD" in result.errors[0]

    def test_optional_field_without_value_is_skipped(self, generator):
        fields = [GenerateField(key="OPTIONAL_VAR")]
        result = generator.generate(fields)
        assert "OPTIONAL_VAR" in result.skipped
        assert "OPTIONAL_VAR" not in result.generated

    def test_override_takes_precedence_over_default(self, generator):
        fields = [GenerateField(key="APP_ENV", default="staging")]
        result = generator.generate(fields, overrides={"APP_ENV": "production"})
        assert result.generated["APP_ENV"] == "production"

    def test_override_takes_precedence_over_auto(self, generator):
        fields = [GenerateField(key="SECRET", auto="secret")]
        result = generator.generate(fields, overrides={"SECRET": "fixed-value"})
        assert result.generated["SECRET"] == "fixed-value"

    def test_multiple_fields_mixed(self, generator):
        fields = [
            GenerateField(key="APP_ENV", default="dev"),
            GenerateField(key="SECRET", auto="secret"),
            GenerateField(key="OPTIONAL"),
            GenerateField(key="REQUIRED", required=True),
        ]
        result = generator.generate(fields)
        assert result.generated["APP_ENV"] == "dev"
        assert "SECRET" in result.generated
        assert "OPTIONAL" in result.skipped
        assert result.has_errors
        assert len(result.errors) == 1

    def test_two_secrets_are_different(self, generator):
        fields = [
            GenerateField(key="S1", auto="secret"),
            GenerateField(key="S2", auto="secret"),
        ]
        result = generator.generate(fields)
        assert result.generated["S1"] != result.generated["S2"]
