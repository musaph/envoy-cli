import pytest
from envoy.env_capitalize import CapitalizeChange, CapitalizeResult, EnvCapitalizer


@pytest.fixture
def capitalizer():
    return EnvCapitalizer()


@pytest.fixture
def selective_capitalizer():
    return EnvCapitalizer(only_keys=["GREETING", "TITLE"])


@pytest.fixture
def sample_vars():
    return {
        "GREETING": "hello world",
        "STATUS": "active",
        "TITLE": "engineer",
        "EMPTY": "",
    }


class TestCapitalizeResult:
    def test_repr(self):
        r = CapitalizeResult(vars={"A": "B"}, changes=[])
        assert "CapitalizeResult" in repr(r)
        assert "total=1" in repr(r)
        assert "changed=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = CapitalizeResult(vars={}, changes=[])
        assert r.has_changes is False

    def test_has_changes_true_when_populated(self):
        change = CapitalizeChange(key="X", old_value="hello", new_value="Hello")
        r = CapitalizeResult(vars={"X": "Hello"}, changes=[change])
        assert r.has_changes is True

    def test_changed_keys_returns_keys(self):
        changes = [
            CapitalizeChange(key="A", old_value="abc", new_value="Abc"),
            CapitalizeChange(key="B", old_value="xyz", new_value="Xyz"),
        ]
        r = CapitalizeResult(vars={"A": "Abc", "B": "Xyz"}, changes=changes)
        assert r.changed_keys == ["A", "B"]


class TestEnvCapitalizer:
    def test_capitalizes_all_values(self, capitalizer, sample_vars):
        result = capitalizer.capitalize(sample_vars)
        assert result.vars["GREETING"] == "Hello world"
        assert result.vars["STATUS"] == "Active"
        assert result.vars["TITLE"] == "Engineer"

    def test_empty_value_unchanged(self, capitalizer, sample_vars):
        result = capitalizer.capitalize(sample_vars)
        assert result.vars["EMPTY"] == ""

    def test_already_capitalized_no_change(self, capitalizer):
        vars = {"MSG": "Hello"}
        result = capitalizer.capitalize(vars)
        assert not result.has_changes

    def test_changes_recorded(self, capitalizer, sample_vars):
        result = capitalizer.capitalize(sample_vars)
        assert result.has_changes
        assert "GREETING" in result.changed_keys
        assert "STATUS" in result.changed_keys

    def test_selective_only_affects_specified_keys(self, selective_capitalizer, sample_vars):
        result = selective_capitalizer.capitalize(sample_vars)
        assert result.vars["GREETING"] == "Hello world"
        assert result.vars["TITLE"] == "Engineer"
        assert result.vars["STATUS"] == "active"  # not in only_keys

    def test_empty_vars_returns_empty_result(self, capitalizer):
        result = capitalizer.capitalize({})
        assert result.vars == {}
        assert not result.has_changes

    def test_change_repr(self):
        c = CapitalizeChange(key="K", old_value="foo", new_value="Foo")
        assert "CapitalizeChange" in repr(c)
        assert "K" in repr(c)
