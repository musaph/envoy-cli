"""Tests for envoy.compress module."""

import pytest
from envoy.compress import EnvCompressor, CompressResult


@pytest.fixture
def compressor() -> EnvCompressor:
    return EnvCompressor()


class TestEnvCompressor:
    def test_compress_decompress_roundtrip(self, compressor):
        original = b"DATABASE_URL=postgres://localhost/mydb\nSECRET_KEY=abc123"
        compressed = compressor.compress(original)
        result = compressor.decompress(compressed)
        assert result == original

    def test_compress_reduces_size_for_large_input(self, compressor):
        original = (b"KEY=value\n") * 200
        compressed = compressor.compress(original)
        assert len(compressed) < len(original)

    def test_compress_vars_roundtrip(self, compressor):
        vars_dict = {"DB_HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
        compressed = compressor.compress_vars(vars_dict)
        result = compressor.decompress_vars(compressed)
        assert result == vars_dict

    def test_compress_vars_empty_dict(self, compressor):
        result = compressor.decompress_vars(compressor.compress_vars({}))
        assert result == {}

    def test_stats_returns_compress_result(self, compressor):
        original = b"A=1\nB=2\nC=3"
        compressed = compressor.compress(original)
        stats = compressor.stats(original, compressed)
        assert isinstance(stats, CompressResult)
        assert stats.original_size == len(original)
        assert stats.compressed_size == len(compressed)
        assert stats.ratio > 0

    def test_stats_empty_original_no_division_error(self, compressor):
        compressed = compressor.compress(b"")
        stats = compressor.stats(b"", compressed)
        assert stats.ratio == 1.0

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError, match="Compression level"):
            EnvCompressor(level=10)

    def test_level_zero_allowed(self):
        c = EnvCompressor(level=0)
        data = b"KEY=value"
        assert c.decompress(c.compress(data)) == data

    def test_decompress_invalid_data_raises(self, compressor):
        with pytest.raises(Exception):
            compressor.decompress(b"not-valid-base64-or-zlib!!!")

    def test_compress_result_repr(self):
        r = CompressResult(original_size=100, compressed_size=60, ratio=0.6)
        assert "100B" in repr(r)
        assert "60B" in repr(r)
        assert "0.60" in repr(r)

    def test_vars_with_equals_in_value(self, compressor):
        vars_dict = {"TOKEN": "abc=def=ghi"}
        result = compressor.decompress_vars(compressor.compress_vars(vars_dict))
        assert result["TOKEN"] == "abc=def=ghi"
