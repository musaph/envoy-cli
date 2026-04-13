"""Unit tests for envoy.template."""
import pytest
from envoy.template import EnvTemplate, TemplateVariable


class TestTemplateVariables:
    def test_no_placeholders(self):
        tmpl = EnvTemplate("DB_HOST=localhost\nDB_PORT=5432\n")
        assert tmpl.variables() == []

    def test_single_required_variable(self):
        tmpl = EnvTemplate("DB_PASS=${DB_PASSWORD}\n")
        variables = tmpl.variables()
        assert len(variables) == 1
        assert variables[0].name == "DB_PASSWORD"
        assert variables[0].required is True
        assert variables[0].default is None

    def test_variable_with_default(self):
        tmpl = EnvTemplate("LOG_LEVEL=${LOG_LEVEL:-info}\n")
        variables = tmpl.variables()
        assert len(variables) == 1
        assert variables[0].name == "LOG_LEVEL"
        assert variables[0].required is False
        assert variables[0].default == "info"

    def test_duplicate_variables_deduplicated(self):
        tmpl = EnvTemplate("A=${FOO}\nB=${FOO}\n")
        assert len(tmpl.variables()) == 1

    def test_multiple_variables(self):
        tmpl = EnvTemplate("A=${X}\nB=${Y:-y}\nC=${Z}\n")
        names = [v.name for v in tmpl.variables()]
        assert names == ["X", "Y", "Z"]

    def test_variable_with_empty_string_default(self):
        """A default of empty string should be treated as optional (not required)."""
        tmpl = EnvTemplate("OPTIONAL=${OPTIONAL:-}\n")
        variables = tmpl.variables()
        assert len(variables) == 1
        assert variables[0].name == "OPTIONAL"
        assert variables[0].required is False
        assert variables[0].default == ""


class TestTemplateRender:
    def test_render_required_variable(self):
        tmpl = EnvTemplate("DB_PASS=${DB_PASSWORD}\n")
        result = tmpl.render({"DB_PASSWORD": "secret"})
        assert result == "DB_PASS=secret\n"

    def test_render_uses_default_when_missing(self):
        tmpl = EnvTemplate("LOG_LEVEL=${LOG_LEVEL:-info}\n")
        result = tmpl.render({})
        assert result == "LOG_LEVEL=info\n"

    def test_render_context_overrides_default(self):
        tmpl = EnvTemplate("LOG_LEVEL=${LOG_LEVEL:-info}\n")
        result = tmpl.render({"LOG_LEVEL": "debug"})
        assert result == "LOG_LEVEL=debug\n"

    def test_render_raises_on_missing_required(self):
        tmpl = EnvTemplate("DB_PASS=${DB_PASSWORD}\n")
        with pytest.raises(KeyError, match="DB_PASSWORD"):
            tmpl.render({})

    def test_render_multiple_substitutions(self):
        tmpl = EnvTemplate("HOST=${HOST}\nPORT=${PORT:-5432}\n")
        result = tmpl.render({"HOST": "db.local"})
        assert result == "HOST=db.local\nPORT=5432\n"

    def test_render_empty_string_default(self):
        """Rendering a variable with an empty default should produce an empty value."""
        tmpl = EnvTemplate("OPTIONAL=${OPTIONAL:-}\n")
        result = tmpl.render({})
        assert result == "OPTIONAL=\n"

    def test_missing_variables_returns_names(self):
        tmpl = EnvTemplate("A=${X}\nB=${Y}\nC=${Z:-z}\n")
        missing = tmpl.missing_variables({"X": "1"})
        assert missing == ["Y"]

    def test_no_missing_variables(self):
        tmpl = EnvTemplate("A=${X}\nB=${Y:-y}\n")
        assert tmpl.missing_variables({"X": "1"}) == []
