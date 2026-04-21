import pytest
from envoy.env_wrap import EnvWrapper, WrapResult, WrapChange


@pytest.fixture
def wrapper():
    return EnvWrapper(width=10)


@pytest.fixture
def wide_wrapper():
    return EnvWrapper(width=40, continuation="\\")


@pytest.fixture
def sample_vars():
    return {
        "SHORT": "hi",
        "EXACT": "1234567890",
        "LONG": "abcdefghijklmnopqrstuvwxyz",
        "VERY_LONG": "A" * 50,
    }


class TestWrapResult:
    def test_repr(self):
        r = WrapResult(changes=[WrapChange("K", "old", "new")], skipped=["X"])
        assert "WrapResult" in repr(r)
        assert "1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = WrapResult()
        assert not r.has_changes()

    def test_has_changes_true_when_populated(self):
        r = WrapResult(changes=[WrapChange("K", "old", "new")])
        assert r.has_changes()

    def test_changed_keys_returns_keys(self):
        r = WrapResult(changes=[WrapChange("A", "x", "y"), WrapChange("B", "x", "y")])
        assert r.changed_keys() == ["A", "B"]


class TestWrapChange:
    def test_repr_contains_key(self):
        c = WrapChange(key="MY_KEY", original="short", wrapped="short")
        assert "MY_KEY" in repr(c)


class TestEnvWrapper:
    def test_short_values_not_wrapped(self, wrapper):
        result = wrapper.wrap({"K": "short"})
        assert not result.has_changes()

    def test_exact_width_not_wrapped(self, wrapper):
        result = wrapper.wrap({"K": "1234567890"})
        assert not result.has_changes()

    def test_long_value_is_wrapped(self, wrapper):
        result = wrapper.wrap({"K": "abcdefghijklmnop"})
        assert result.has_changes()
        assert "K" in result.changed_keys()

    def test_wrapped_value_contains_continuation(self, wrapper):
        result = wrapper.wrap({"K": "abcdefghijklmnop"})
        change = result.changes[0]
        assert "\\" in change.wrapped

    def test_skip_keys_excluded(self):
        w = EnvWrapper(width=5, skip_keys=["SKIP"])
        result = w.wrap({"SKIP": "toolongvalue", "OTHER": "toolongvalue"})
        assert "SKIP" in result.skipped
        assert "OTHER" in result.changed_keys()

    def test_apply_returns_modified_dict(self, wrapper):
        vars = {"K": "abcdefghijklmnop", "S": "hi"}
        out = wrapper.apply(vars)
        assert out["S"] == "hi"
        assert "\\" in out["K"]

    def test_apply_preserves_unchanged_keys(self, wrapper, sample_vars):
        out = wrapper.apply(sample_vars)
        assert out["SHORT"] == "hi"
        assert out["EXACT"] == "1234567890"

    def test_invalid_width_raises(self):
        with pytest.raises(ValueError):
            EnvWrapper(width=0)

    def test_multiple_wraps_for_very_long_value(self):
        w = EnvWrapper(width=10)
        result = w.wrap({"K": "A" * 35})
        change = result.changes[0]
        assert change.wrapped.count("\\") >= 2

    def test_custom_continuation_character(self):
        w = EnvWrapper(width=5, continuation="|")
        result = w.wrap({"K": "abcdefghij"})
        assert "|" in result.changes[0].wrapped
