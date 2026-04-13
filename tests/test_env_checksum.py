"""Tests for envoy.env_checksum."""
import pytest
from envoy.env_checksum import ChecksumResult, EnvChecksummer


@pytest.fixture
def checksummer() -> EnvChecksummer:
    return EnvChecksummer()


@pytest.fixture
def sample_vars() -> dict:
    return {"APP_ENV": "production", "DB_HOST": "localhost", "PORT": "5432"}


# ---------------------------------------------------------------------------
# ChecksumResult
# ---------------------------------------------------------------------------

class TestChecksumResult:
    def test_repr(self):
        r = ChecksumResult(checksum="abc", algorithm="sha256", key_count=3)
        assert "sha256" in repr(r)
        assert "key_count=3" in repr(r)

    def test_is_valid_no_mismatches(self):
        r = ChecksumResult(checksum="abc", key_count=1)
        assert r.is_valid is True

    def test_is_invalid_with_mismatches(self):
        r = ChecksumResult(checksum="abc", key_count=1, mismatches=["<checksum mismatch>"])
        assert r.is_valid is False


# ---------------------------------------------------------------------------
# EnvChecksummer – construction
# ---------------------------------------------------------------------------

class TestEnvChecksummerInit:
    def test_default_algorithm_is_sha256(self):
        c = EnvChecksummer()
        assert c.algorithm == "sha256"

    def test_accepts_sha1(self):
        c = EnvChecksummer(algorithm="sha1")
        assert c.algorithm == "sha1"

    def test_accepts_md5(self):
        c = EnvChecksummer(algorithm="md5")
        assert c.algorithm == "md5"

    def test_rejects_unknown_algorithm(self):
        with pytest.raises(ValueError, match="Unsupported"):
            EnvChecksummer(algorithm="blake2b")


# ---------------------------------------------------------------------------
# EnvChecksummer – compute
# ---------------------------------------------------------------------------

class TestCompute:
    def test_returns_checksum_result(self, checksummer, sample_vars):
        result = checksummer.compute(sample_vars)
        assert isinstance(result, ChecksumResult)

    def test_key_count_matches_input(self, checksummer, sample_vars):
        result = checksummer.compute(sample_vars)
        assert result.key_count == len(sample_vars)

    def test_checksum_is_hex_string(self, checksummer, sample_vars):
        result = checksummer.compute(sample_vars)
        int(result.checksum, 16)  # should not raise

    def test_same_vars_same_checksum(self, checksummer, sample_vars):
        r1 = checksummer.compute(sample_vars)
        r2 = checksummer.compute(dict(sample_vars))  # copy
        assert r1.checksum == r2.checksum

    def test_different_vars_different_checksum(self, checksummer, sample_vars):
        r1 = checksummer.compute(sample_vars)
        modified = {**sample_vars, "PORT": "9999"}
        r2 = checksummer.compute(modified)
        assert r1.checksum != r2.checksum

    def test_order_independent(self, checksummer):
        a = checksummer.compute({"X": "1", "Y": "2"})
        b = checksummer.compute({"Y": "2", "X": "1"})
        assert a.checksum == b.checksum

    def test_empty_vars_produces_checksum(self, checksummer):
        result = checksummer.compute({})
        assert result.checksum
        assert result.key_count == 0


# ---------------------------------------------------------------------------
# EnvChecksummer – verify
# ---------------------------------------------------------------------------

class TestVerify:
    def test_valid_when_checksum_matches(self, checksummer, sample_vars):
        expected = checksummer.compute(sample_vars).checksum
        result = checksummer.verify(sample_vars, expected)
        assert result.is_valid is True
        assert result.mismatches == []

    def test_invalid_when_vars_changed(self, checksummer, sample_vars):
        expected = checksummer.compute(sample_vars).checksum
        tampered = {**sample_vars, "APP_ENV": "staging"}
        result = checksummer.verify(tampered, expected)
        assert result.is_valid is False
        assert len(result.mismatches) == 1

    def test_invalid_when_expected_is_wrong(self, checksummer, sample_vars):
        result = checksummer.verify(sample_vars, "deadbeef")
        assert result.is_valid is False

    def test_verify_returns_actual_checksum(self, checksummer, sample_vars):
        expected = checksummer.compute(sample_vars).checksum
        result = checksummer.verify(sample_vars, expected)
        assert result.checksum == expected
