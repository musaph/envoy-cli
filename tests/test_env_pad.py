"""Tests for EnvPadder."""
import pytest
from envoy.env_pad import EnvPadder, PadChange, PadResult


@pytest.fixture
def padder() -> EnvPadder:
    return EnvPadder(min_length=6, fill_char="0", align="right")


@pytest.fixture
def left_padder() -> EnvPadder:
    return EnvPadder(min_length=6, fill_char="_", align="left")


@pytest.fixture
def sample_vars():
    return {"PORT": "80", "TIMEOUT": "30", "LONG_VALUE": "1234567"}


class TestPadResult:
    def test_repr(self):
        r = PadResult(changes=[PadChange("K", "v", "0000v", "0")], vars={"K": "0000v"})
        assert "PadResult" in repr(r)
        assert "1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = PadResult()
        assert r.has_changes() is False

    def test_has_changes_true_when_populated(self):
        r = PadResult(changes=[PadChange("K", "v", "00000v", "0")])
        assert r.has_changes() is True

    def test_changed_keys(self):
        r = PadResult(changes=[PadChange("A", "1", "000001", "0"), PadChange("B", "2", "000002", "0")])
        assert r.changed_keys() == ["A", "B"]


class TestEnvPadder:
    def test_pads_short_values_right(self, padder, sample_vars):
        result = padder.pad(sample_vars)
        assert result.vars["PORT"] == "000080"
        assert result.vars["TIMEOUT"] == "000030"

    def test_does_not_pad_long_values(self, padder, sample_vars):
        result = padder.pad(sample_vars)
        assert result.vars["LONG_VALUE"] == "1234567"

    def test_pads_left_align(self, left_padder):
        result = left_padder.pad({"KEY": "hi"})
        assert result.vars["KEY"] == "hi____"

    def test_changes_recorded(self, padder, sample_vars):
        result = padder.pad(sample_vars)
        changed = result.changed_keys()
        assert "PORT" in changed
        assert "TIMEOUT" in changed
        assert "LONG_VALUE" not in changed

    def test_specific_keys_only(self):
        p = EnvPadder(min_length=5, fill_char="x", align="left", keys=["A"])
        result = p.pad({"A": "1", "B": "2"})
        assert result.vars["A"] == "1xxxx"
        assert result.vars["B"] == "2"  # untouched

    def test_empty_vars(self, padder):
        result = padder.pad({})
        assert result.vars == {}
        assert result.has_changes() is False

    def test_value_exactly_min_length_not_changed(self, padder):
        result = padder.pad({"KEY": "123456"})
        assert result.vars["KEY"] == "123456"
        assert "KEY" not in result.changed_keys()

    def test_invalid_fill_char_raises(self):
        with pytest.raises(ValueError, match="fill_char"):
            EnvPadder(fill_char="ab")

    def test_invalid_align_raises(self):
        with pytest.raises(ValueError, match="align"):
            EnvPadder(align="center")

    def test_pad_change_repr(self):
        c = PadChange(key="K", original="v", padded="00000v", fill_char="0")
        assert "PadChange" in repr(c)
        assert "K" in repr(c)
