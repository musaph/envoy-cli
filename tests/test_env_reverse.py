import pytest
from envoy.env_reverse import EnvReverser, ReverseChange, ReverseResult


@pytest.fixture
def reverser():
    return EnvReverser()


@pytest.fixture
def selective_reverser():
    return EnvReverser(keys=["SECRET", "TOKEN"])


@pytest.fixture
def sample_vars():
    return {
        "APP_NAME": "envoy",
        "SECRET": "abc123",
        "TOKEN": "xyz",
        "PORT": "8080",
    }


class TestReverseResult:
    def test_repr(self):
        r = ReverseResult(vars={"A": "1"}, changes=[])
        assert "ReverseResult" in repr(r)
        assert "changed=0" in repr(r)
        assert "total=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = ReverseResult()
        assert r.has_changes() is False

    def test_has_changes_true_when_populated(self):
        c = ReverseChange(key="A", original="hello", reversed_value="olleh")
        r = ReverseResult(vars={"A": "olleh"}, changes=[c])
        assert r.has_changes() is True

    def test_changed_keys(self):
        c = ReverseChange(key="FOO", original="bar", reversed_value="rab")
        r = ReverseResult(vars={"FOO": "rab"}, changes=[c])
        assert r.changed_keys() == ["FOO"]


class TestReverseChange:
    def test_repr_contains_key_and_values(self):
        c = ReverseChange(key="KEY", original="abc", reversed_value="cba")
        assert "KEY" in repr(c)
        assert "abc" in repr(c)
        assert "cba" in repr(c)


class TestEnvReverser:
    def test_reverses_all_values(self, reverser, sample_vars):
        result = reverser.reverse(sample_vars)
        assert result.vars["APP_NAME"] == "yovne"
        assert result.vars["SECRET"] == "321cba"
        assert result.vars["PORT"] == "0808"

    def test_palindrome_produces_no_change(self, reverser):
        vars = {"KEY": "racecar"}
        result = reverser.reverse(vars)
        assert result.vars["KEY"] == "racecar"
        assert not result.has_changes()

    def test_selective_reverser_only_touches_specified_keys(self, selective_reverser, sample_vars):
        result = selective_reverser.reverse(sample_vars)
        assert result.vars["SECRET"] == "321cba"
        assert result.vars["TOKEN"] == "zyx"
        assert result.vars["APP_NAME"] == "envoy"  # unchanged
        assert result.vars["PORT"] == "8080"  # unchanged

    def test_selective_reverser_changes_only_target_keys(self, selective_reverser, sample_vars):
        result = selective_reverser.reverse(sample_vars)
        changed = result.changed_keys()
        assert "SECRET" in changed
        assert "TOKEN" in changed
        assert "APP_NAME" not in changed
        assert "PORT" not in changed

    def test_empty_value_reversed_is_still_empty(self, reverser):
        vars = {"EMPTY": ""}
        result = reverser.reverse(vars)
        assert result.vars["EMPTY"] == ""
        assert not result.has_changes()

    def test_single_char_value_unchanged(self, reverser):
        vars = {"X": "a"}
        result = reverser.reverse(vars)
        assert result.vars["X"] == "a"
        assert not result.has_changes()

    def test_original_vars_not_mutated(self, reverser, sample_vars):
        original_copy = dict(sample_vars)
        reverser.reverse(sample_vars)
        assert sample_vars == original_copy
