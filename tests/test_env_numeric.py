import pytest
from envoy.env_numeric import EnvNumeric, NumericResult, NumericChange


@pytest.fixture
def rounder():
    return EnvNumeric(operation="round", precision=0)


@pytest.fixture
def incrementer():
    return EnvNumeric(operation="increment", step=1.0)


@pytest.fixture
def sample_vars():
    return {"PORT": "8080", "TIMEOUT": "30.7", "NAME": "alice", "RETRIES": "3"}


class TestNumericResult:
    def test_repr(self):
        r = NumericResult()
        assert "NumericResult" in repr(r)
        assert "changes=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert not NumericResult().has_changes()

    def test_has_changes_true_when_populated(self):
        r = NumericResult(changes=[NumericChange("X", "1.5", "2", "round")])
        assert r.has_changes()

    def test_has_errors_false_when_empty(self):
        assert not NumericResult().has_errors()

    def test_changed_keys_returns_list(self):
        r = NumericResult(changes=[
            NumericChange("A", "1.1", "1", "round"),
            NumericChange("B", "2.9", "3", "round"),
        ])
        assert r.changed_keys() == ["A", "B"]


class TestEnvNumericRound:
    def test_rounds_float_to_int(self, rounder, sample_vars):
        result = rounder.process(sample_vars)
        keys = result.changed_keys()
        assert "TIMEOUT" in keys

    def test_skips_non_numeric(self, rounder, sample_vars):
        result = rounder.process(sample_vars)
        assert "NAME" in result.skipped

    def test_integer_value_unchanged(self, rounder, sample_vars):
        result = rounder.process(sample_vars)
        assert "PORT" not in result.changed_keys()

    def test_apply_returns_modified_dict(self, rounder, sample_vars):
        out = rounder.apply(sample_vars)
        assert out["TIMEOUT"] == "31"
        assert out["NAME"] == "alice"


class TestEnvNumericIncrement:
    def test_increments_integer(self, incrementer):
        out = incrementer.apply({"X": "5"})
        assert out["X"] == "6"

    def test_increments_float(self):
        inc = EnvNumeric(operation="increment", step=0.5)
        out = inc.apply({"X": "1.0"})
        assert out["X"] == "1.5"

    def test_decrement(self):
        dec = EnvNumeric(operation="decrement", step=2.0)
        out = dec.apply({"X": "10"})
        assert out["X"] == "8"


class TestEnvNumericAbs:
    def test_abs_negative(self):
        proc = EnvNumeric(operation="abs")
        out = proc.apply({"TEMP": "-42"})
        assert out["TEMP"] == "42"

    def test_abs_positive_unchanged(self):
        proc = EnvNumeric(operation="abs")
        result = proc.process({"TEMP": "42"})
        assert not result.has_changes()


class TestEnvNumericNegate:
    def test_negate_positive(self):
        proc = EnvNumeric(operation="negate")
        out = proc.apply({"X": "5"})
        assert out["X"] == "-5"


class TestEnvNumericKeyFilter:
    def test_only_specified_keys_processed(self, sample_vars):
        proc = EnvNumeric(operation="increment", step=1.0, keys=["PORT"])
        result = proc.process(sample_vars)
        assert result.changed_keys() == ["PORT"]
        assert "TIMEOUT" in result.skipped


class TestEnvNumericInvalidOperation:
    def test_raises_on_unknown_operation(self):
        with pytest.raises(ValueError, match="Unknown operation"):
            EnvNumeric(operation="multiply")
