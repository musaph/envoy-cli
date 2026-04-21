import pytest
from envoy.env_unescape import EnvUnescaper, UnescapeChange, UnescapeResult


@pytest.fixture
def unescaper():
    return EnvUnescaper()


@pytest.fixture
def selective_unescaper():
    return EnvUnescaper(keys=["MSG", "PATH"])


@pytest.fixture
def sample_vars():
    return {
        "MSG": r"Hello\nWorld",
        "TAB": r"col1\tcol2",
        "SAFE": "no_escapes_here",
        "PATH": r"C:\\Users\\admin",
    }


class TestUnescapeResult:
    def test_repr(self):
        result = UnescapeResult(vars={"A": "b"}, changes=[])
        assert "changed=0" in repr(result)
        assert "total=1" in repr(result)

    def test_has_changes_false_when_empty(self):
        result = UnescapeResult(vars={}, changes=[])
        assert result.has_changes() is False

    def test_has_changes_true_when_populated(self):
        change = UnescapeChange(key="K", original=r"\n", unescaped="\n")
        result = UnescapeResult(vars={"K": "\n"}, changes=[change])
        assert result.has_changes() is True

    def test_changed_keys_returns_list(self):
        change = UnescapeChange(key="X", original=r"\t", unescaped="\t")
        result = UnescapeResult(vars={"X": "\t"}, changes=[change])
        assert result.changed_keys() == ["X"]


class TestUnescapeChange:
    def test_repr_contains_key(self):
        c = UnescapeChange(key="FOO", original=r"\n", unescaped="\n")
        assert "FOO" in repr(c)


class TestEnvUnescaper:
    def test_no_escapes_unchanged(self, unescaper):
        result = unescaper.unescape({"SAFE": "hello"})
        assert result.vars["SAFE"] == "hello"
        assert not result.has_changes()

    def test_newline_unescaped(self, unescaper):
        result = unescaper.unescape({"MSG": r"line1\nline2"})
        assert result.vars["MSG"] == "line1\nline2"
        assert result.has_changes()

    def test_tab_unescaped(self, unescaper):
        result = unescaper.unescape({"V": r"a\tb"})
        assert result.vars["V"] == "a\tb"

    def test_carriage_return_unescaped(self, unescaper):
        result = unescaper.unescape({"V": r"a\rb"})
        assert result.vars["V"] == "a\rb"

    def test_double_backslash_unescaped(self, unescaper):
        result = unescaper.unescape({"V": r"C:\\Users"})
        assert result.vars["V"] == "C:\\Users"

    def test_multiple_keys(self, unescaper, sample_vars):
        result = unescaper.unescape(sample_vars)
        assert result.vars["MSG"] == "Hello\nWorld"
        assert result.vars["TAB"] == "col1\tcol2"
        assert result.vars["SAFE"] == "no_escapes_here"
        assert len(result.changes) == 3

    def test_selective_only_processes_listed_keys(self, selective_unescaper, sample_vars):
        result = selective_unescaper.unescape(sample_vars)
        assert result.vars["MSG"] == "Hello\nWorld"
        assert result.vars["TAB"] == r"col1\tcol2"  # not in selective keys
        assert "MSG" in result.changed_keys()
        assert "TAB" not in result.changed_keys()

    def test_empty_vars_returns_empty_result(self, unescaper):
        result = unescaper.unescape({})
        assert result.vars == {}
        assert not result.has_changes()
