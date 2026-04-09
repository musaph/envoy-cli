"""Integration tests: template + parser + serializer roundtrip."""
import pytest
from envoy.template import EnvTemplate
from envoy.parser import EnvParser


SAMPLE_TEMPLATE = """\
# Database configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}

# App settings
DEBUG=${DEBUG:-false}
SECRET_KEY=${SECRET_KEY}
"""


class TestTemplateWithParser:
    def test_render_then_parse_roundtrip(self):
        tmpl = EnvTemplate(SAMPLE_TEMPLATE)
        context = {
            "DB_NAME": "mydb",
            "DB_USER": "admin",
            "DB_PASS": "s3cr3t",
            "SECRET_KEY": "abc123",
        }
        rendered = tmpl.render(context)
        parsed = EnvParser.parse(rendered)
        assert parsed["DB_HOST"] == "localhost"
        assert parsed["DB_PORT"] == "5432"
        assert parsed["DB_NAME"] == "mydb"
        assert parsed["DB_USER"] == "admin"
        assert parsed["DB_PASS"] == "s3cr3t"
        assert parsed["DEBUG"] == "false"
        assert parsed["SECRET_KEY"] == "abc123"

    def test_all_required_variables_detected(self):
        tmpl = EnvTemplate(SAMPLE_TEMPLATE)
        required = [v.name for v in tmpl.variables() if v.required]
        assert set(required) == {"DB_NAME", "DB_USER", "DB_PASS", "SECRET_KEY"}

    def test_optional_variables_have_defaults(self):
        tmpl = EnvTemplate(SAMPLE_TEMPLATE)
        optional = {v.name: v.default for v in tmpl.variables() if not v.required}
        assert optional["DB_HOST"] == "localhost"
        assert optional["DB_PORT"] == "5432"
        assert optional["DEBUG"] == "false"

    def test_partial_context_uses_defaults(self):
        tmpl = EnvTemplate(SAMPLE_TEMPLATE)
        context = {
            "DB_NAME": "testdb",
            "DB_USER": "tester",
            "DB_PASS": "pass",
            "SECRET_KEY": "key",
        }
        rendered = tmpl.render(context)
        parsed = EnvParser.parse(rendered)
        assert parsed["DB_HOST"] == "localhost"
        assert parsed["DEBUG"] == "false"

    def test_missing_required_raises_key_error(self):
        tmpl = EnvTemplate(SAMPLE_TEMPLATE)
        with pytest.raises(KeyError):
            tmpl.render({"DB_NAME": "x"})
