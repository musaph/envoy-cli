"""Tests for envoy.validator module."""

import pytest
from envoy.validator import EnvValidator, ValidationResult, ValidationIssue


@pytest.fixture
def validator():
    return EnvValidator()


class TestValidationResult:
    def test_is_valid_with_no_issues(self):
        result = ValidationResult()
        assert result.is_valid is True

    def test_is_invalid_with_error(self):
        result = ValidationResult()
        result.add('KEY', 'some error')
        assert result.is_valid is False

    def test_warnings_do_not_affect_validity(self):
        result = ValidationResult()
        result.add('key', 'lowercase key', severity='warning')
        assert result.is_valid is True

    def test_errors_and_warnings_separated(self):
        result = ValidationResult()
        result.add('BAD KEY', 'invalid char', severity='error')
        result.add('good_key', 'lowercase', severity='warning')
        assert len(result.errors) == 1
        assert len(result.warnings) == 1


class TestEnvValidator:
    def test_valid_variables_pass(self, validator):
        variables = {'DATABASE_URL': 'postgres://localhost/db', 'PORT': '5432'}
        result = validator.validate(variables)
        assert result.is_valid
        assert result.issues == []

    def test_empty_dict_produces_warning(self, validator):
        result = validator.validate({})
        assert result.is_valid  # no errors
        assert len(result.warnings) == 1
        assert '__file__' in result.warnings[0].key

    def test_invalid_key_characters(self, validator):
        result = validator.validate({'INVALID-KEY': 'value'})
        assert not result.is_valid
        assert any('invalid characters' in i.message for i in result.errors)

    def test_lowercase_key_produces_warning(self, validator):
        result = validator.validate({'my_var': 'hello'})
        assert result.is_valid
        assert any('uppercase' in i.message for i in result.warnings)

    def test_empty_secret_value_produces_warning(self, validator):
        result = validator.validate({'API_SECRET': ''})
        assert result.is_valid
        assert any('secret' in i.message.lower() for i in result.warnings)

    def test_empty_non_secret_value_no_warning(self, validator):
        result = validator.validate({'APP_NAME': ''})
        assert result.is_valid
        assert result.warnings == []

    def test_multiple_issues_collected(self, validator):
        variables = {
            'invalid key': 'value',
            'lowercase': 'val',
            'API_TOKEN': '',
        }
        result = validator.validate(variables)
        assert len(result.errors) >= 1
        assert len(result.warnings) >= 2

    def test_valid_key_with_numbers(self, validator):
        result = validator.validate({'VAR_123': 'value'})
        assert result.is_valid
        assert result.errors == []

    def test_key_starting_with_number_is_invalid(self, validator):
        result = validator.validate({'1VAR': 'value'})
        assert not result.is_valid
