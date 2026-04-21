"""Tests for envoy.env_hash."""
import hashlib
import pytest
from envoy.env_hash import EnvHasher, HashChange, HashResult, SUPPORTED_ALGORITHMS


@pytest.fixture
def hasher():
    return EnvHasher(algorithm="sha256")


@pytest.fixture
def selective_hasher():
    return EnvHasher(algorithm="sha256", keys=["SECRET", "TOKEN"])


@pytest.fixture
def sample_vars():
    return {"SECRET": "mysecret", "TOKEN": "abc123", "APP_NAME": "envoy"}


class TestHashResult:
    def test_repr(self):
        r = HashResult(changes=[HashChange("K", "v", "h", "sha256")], skipped=["X"])
        assert "changed=1" in repr(r)
        assert "skipped=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert HashResult().has_changes() is False

    def test_has_changes_true_when_populated(self):
        r = HashResult(changes=[HashChange("K", "v", "h", "sha256")])
        assert r.has_changes() is True

    def test_changed_keys(self):
        r = HashResult(
            changes=[
                HashChange("A", "1", "h1", "sha256"),
                HashChange("B", "2", "h2", "sha256"),
            ]
        )
        assert r.changed_keys() == ["A", "B"]


class TestHashChange:
    def test_repr_contains_key_and_algorithm(self):
        c = HashChange("MY_KEY", "value", "deadbeef", "md5")
        assert "MY_KEY" in repr(c)
        assert "md5" in repr(c)


class TestEnvHasher:
    def test_invalid_algorithm_raises(self):
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            EnvHasher(algorithm="crc32")

    def test_all_supported_algorithms_accepted(self):
        for algo in SUPPORTED_ALGORITHMS:
            h = EnvHasher(algorithm=algo)
            assert h.algorithm == algo

    def test_hash_all_vars(self, hasher, sample_vars):
        result = hasher.hash_vars(sample_vars)
        assert len(result.changes) == 3
        assert result.skipped == []

    def test_hash_produces_correct_sha256(self, hasher):
        result = hasher.hash_vars({"KEY": "hello"})
        expected = hashlib.sha256(b"hello").hexdigest()
        assert result.changes[0].hashed == expected

    def test_selective_hasher_skips_unlisted_keys(self, selective_hasher, sample_vars):
        result = selective_hasher.hash_vars(sample_vars)
        assert result.changed_keys() == ["SECRET", "TOKEN"]
        assert "APP_NAME" in result.skipped

    def test_prefix_prepended_to_hash(self, sample_vars):
        h = EnvHasher(algorithm="sha256", prefix="sha256:")
        result = h.hash_vars({"KEY": "value"})
        assert result.changes[0].hashed.startswith("sha256:")

    def test_apply_returns_modified_dict(self, selective_hasher, sample_vars):
        out = selective_hasher.apply(sample_vars)
        assert out["APP_NAME"] == "envoy"  # unchanged
        assert out["SECRET"] != "mysecret"  # hashed
        assert len(out["SECRET"]) == 64  # sha256 hex length

    def test_md5_hash_length(self):
        h = EnvHasher(algorithm="md5")
        result = h.hash_vars({"K": "v"})
        assert len(result.changes[0].hashed) == 32

    def test_sha512_hash_length(self):
        h = EnvHasher(algorithm="sha512")
        result = h.hash_vars({"K": "v"})
        assert len(result.changes[0].hashed) == 128

    def test_empty_vars_returns_empty_result(self, hasher):
        result = hasher.hash_vars({})
        assert result.has_changes() is False
        assert result.skipped == []
