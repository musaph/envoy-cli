import pytest
from envoy.env_uppercase_keys import (
    EnvUppercaseKeyConverter,
    UppercaseKeyChange,
    UppercaseKeyResult,
)


@pytest.fixture
def converter():
    return EnvUppercaseKeyConverter()


@pytest.fixture
def overwrite_converter():
    return EnvUppercaseKeyConverter(overwrite=True)


@pytest.fixture
def sample_vars():
    return {
        "db_host": "localhost",
        "db_port": "5432",
        "API_KEY": "already-upper",
        "app_name": "envoy",
    }


class TestUppercaseKeyResult:
    def test_repr(self):
        r = UppercaseKeyResult(
            changes=[UppercaseKeyChange("db_host", "DB_HOST", "localhost")],
            skipped=[],
        )
        assert "changes=1" in repr(r)
        assert "skipped=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = UppercaseKeyResult()
        assert r.has_changes is False

    def test_has_changes_true_when_populated(self):
        r = UppercaseKeyResult(
            changes=[UppercaseKeyChange("x", "X", "val")]
        )
        assert r.has_changes is True

    def test_changed_keys_lists_originals(self):
        r = UppercaseKeyResult(
            changes=[
                UppercaseKeyChange("db_host", "DB_HOST", "localhost"),
                UppercaseKeyChange("app_name", "APP_NAME", "envoy"),
            ]
        )
        assert r.changed_keys == ["db_host", "app_name"]

    def test_output_vars_uses_new_keys(self):
        r = UppercaseKeyResult(
            changes=[UppercaseKeyChange("db_host", "DB_HOST", "localhost")]
        )
        assert r.output_vars == {"DB_HOST": "localhost"}


class TestEnvUppercaseKeyConverter:
    def test_already_uppercase_not_in_changes(self, converter):
        result = converter.convert({"API_KEY": "secret"})
        assert result.has_changes is False
        assert result.skipped == []

    def test_lowercase_key_converted(self, converter):
        result = converter.convert({"db_host": "localhost"})
        assert result.has_changes is True
        assert result.changes[0].new_key == "DB_HOST"
        assert result.changes[0].value == "localhost"

    def test_mixed_case_key_converted(self, converter):
        result = converter.convert({"appName": "envoy"})
        assert result.changes[0].new_key == "APPNAME"

    def test_collision_skipped_without_overwrite(self, converter):
        vars = {"DB_HOST": "primary", "db_host": "secondary"}
        result = converter.convert(vars)
        assert "db_host" in result.skipped

    def test_collision_overwritten_with_flag(self, overwrite_converter):
        vars = {"DB_HOST": "primary", "db_host": "secondary"}
        result = overwrite_converter.convert(vars)
        assert "db_host" not in result.skipped
        upper_keys = [c.new_key for c in result.changes]
        assert "DB_HOST" in upper_keys

    def test_full_sample(self, converter, sample_vars):
        result = converter.convert(sample_vars)
        assert result.has_changes is True
        new_keys = [c.new_key for c in result.changes]
        assert "DB_HOST" in new_keys
        assert "DB_PORT" in new_keys
        assert "APP_NAME" in new_keys
        # API_KEY was already uppercase, not in changes
        assert "API_KEY" not in new_keys
