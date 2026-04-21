import pytest
from envoy.env_escape import EscapeChange, EscapeResult, EnvEscaper


@pytest.fixture
def escaper():
    return EnvEscaper()


@pytest.fixture
def selective_escaper():
    return EnvEscaper(keys=["SECRET", "TOKEN"])


@pytest.fixture
def unescaper():
    return EnvEscaper(unescape=True)


@pytest.fixture
def sample_vars():
    return {
        "NAME": "Alice",
        "GREETING": "Hello\nWorld",
        "PATH": "/usr/local\\bin",
        "TAB_VAL": "col1\tcol2",
        "SECRET": "my\nsecret",
    }


class TestEscapeResult:
    def test_repr(self):
        r = EscapeResult(changes=[], vars={})
        assert "EscapeResult" in repr(r)
        assert "changes=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = EscapeResult()
        assert r.has_changes() is False

    def test_has_changes_true_when_populated(self):
        c = EscapeChange(key="K", original="a\nb", escaped="a\\nb")
        r = EscapeResult(changes=[c], vars={"K": "a\\nb"})
        assert r.has_changes() is True

    def test_changed_keys_returns_list(self):
        c = EscapeChange(key="FOO", original="a\nb", escaped="a\\nb")
        r = EscapeResult(changes=[c], vars={})
        assert r.changed_keys() == ["FOO"]


class TestEnvEscaper:
    def test_no_special_chars_no_changes(self, escaper):
        vars = {"NAME": "Alice", "ENV": "production"}
        result = escaper.process(vars)
        assert result.has_changes() is False
        assert result.vars == vars

    def test_escapes_newline(self, escaper):
        vars = {"MSG": "line1\nline2"}
        result = escaper.process(vars)
        assert result.vars["MSG"] == "line1\\nline2"
        assert result.has_changes() is True

    def test_escapes_tab(self, escaper):
        vars = {"DATA": "col1\tcol2"}
        result = escaper.process(vars)
        assert result.vars["DATA"] == "col1\\tcol2"

    def test_escapes_backslash(self, escaper):
        vars = {"PATH": "/usr/local\\bin"}
        result = escaper.process(vars)
        assert result.vars["PATH"] == "/usr/local\\\\bin"

    def test_escapes_carriage_return(self, escaper):
        vars = {"VAL": "foo\rbar"}
        result = escaper.process(vars)
        assert result.vars["VAL"] == "foo\\rbar"

    def test_selective_only_escapes_listed_keys(self, selective_escaper, sample_vars):
        result = selective_escaper.process(sample_vars)
        # GREETING has \n but is not in keys list
        assert result.vars["GREETING"] == sample_vars["GREETING"]
        # SECRET is in keys list
        assert result.vars["SECRET"] == "my\\nsecret"

    def test_unescape_reverses_escape(self, unescaper):
        vars = {"MSG": "line1\\nline2", "TAB": "col1\\tcol2"}
        result = unescaper.process(vars)
        assert result.vars["MSG"] == "line1\nline2"
        assert result.vars["TAB"] == "col1\tcol2"

    def test_escape_unescape_roundtrip(self, escaper, unescaper, sample_vars):
        escaped = escaper.process(sample_vars)
        restored = unescaper.process(escaped.vars)
        assert restored.vars == sample_vars

    def test_change_repr(self):
        c = EscapeChange(key="K", original="a\nb", escaped="a\\nb")
        assert "EscapeChange" in repr(c)
        assert "K" in repr(c)
